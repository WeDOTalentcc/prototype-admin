# frozen_string_literal: true

class DispatchOrchestratorJob < ApplicationJob
  queue_as :default

  BATCH_SIZE = 500
  SCROLL_BATCH = 1000

  def perform(dispatch_id, options = {}, account_id: nil)
    account = Account.find_by(id: account_id) if account_id
    Apartment::Tenant.switch!(account.tenant) if account&.tenant

    dispatch = Dispatch.find_by(id: dispatch_id)
    return unless dispatch&.pending?
    dispatch.processing!
    strategies.fetch(dispatch.target_type, method(:noop)).call(dispatch, options)
    dispatch.completed! unless dispatch.failed?
  rescue StandardError => e
    dispatch.failed! if dispatch&.persisted? && !dispatch&.failed?
    raise e
  end

  private

  def strategies
    @strategies ||= {
      "ids" => method(:process_ids),
      "reference" => method(:process_reference),
      "search" => method(:process_search)
    }
  end

  def noop(_dispatch, _options); end

  def process_ids(dispatch, options)
    candidate_ids = Array(options["candidate_ids"] || dispatch.target_payload["ids"]).map(&:to_i).reject(&:zero?)
    user_ids = Array(options["user_ids"]).map(&:to_i).reject(&:zero?)

    if candidate_ids.any?
      scope = dispatch.account.candidates.where(id: candidate_ids)
      process_scope(scope, dispatch)
    end

    if user_ids.any?
      scope = dispatch.account.users.where(id: user_ids)
      process_scope(scope, dispatch)
    end
  end

  def process_reference(dispatch, _options)
    if dispatch.reference.respond_to?(:candidates)
      scope = dispatch.reference.candidates
      process_scope(scope, dispatch) if scope.exists?
    end

    if dispatch.reference.respond_to?(:users)
      scope = dispatch.reference.users
      process_scope(scope, dispatch) if scope.exists?
    end
  end

  def process_search(dispatch, options)
    payload = options["search"] || dispatch.target_payload || {}
    query = payload["query"].presence || "*"
    search_options = build_search_options(payload)

    if defined?(Searchkick) && Candidate.respond_to?(:search)
      Candidate.search(query, **search_options) do |body|
      end.each_batch do |batch|
        candidates = Candidate.where(id: batch.map(&:id))
        process_batch(candidates, dispatch)
      end
    end

    if defined?(Searchkick) && User.respond_to?(:search)
      User.search(query, **search_options) do |body|
      end.each_batch do |batch|
        users = User.where(id: batch.map(&:id))
        process_batch(users, dispatch)
      end
    end
  rescue => e
    dispatch.failed!
    raise e
  end

  def build_search_options(payload)
    opts = {}
    opts[:where] = payload["where"] if payload["where"].is_a?(Hash)
    opts
  end

  def process_scope(scope, dispatch)
    return unless scope.exists?
    scope.find_in_batches(batch_size: BATCH_SIZE) { |batch| process_batch(batch, dispatch) }
  end

  def process_batch(batch, dispatch)
    rows = build_rows(batch, dispatch)
    return if rows.empty?

    result = DispatchMessage.insert_all(
      rows,
      returning: %i[id]
    )

    message_ids = result.rows.flatten

    enqueue_delivery_jobs(message_ids, account_id: dispatch.account_id)
  end

  def build_rows(batch, dispatch)
    template_subject = dispatch.subject.to_s
    template_body = dispatch.body.to_s

    now = Time.current
    batch.filter_map do |record|
      next unless record.respond_to?(:email)
      next if record.email.blank?

      recipient_type = record.class.name
      personalized_subject = personalize(template_subject, record)
      personalized_body = personalize(template_body, record)
      {
        dispatch_id: dispatch.id,
        account_id: dispatch.account_id,
        recipient_type: recipient_type,
        recipient_id: record.id,
        recipient_address: record.email,
        status: DispatchMessage.statuses[:pending],
        subject: personalized_subject,
        body: personalized_body,
        tracking_pixel_token: SecureRandom.urlsafe_base64(32),
        tracking_click_token: SecureRandom.urlsafe_base64(32),
        created_at: now,
        updated_at: now
      }
    end
  end

  def personalize(template, record)
    result = template.dup

    if record.is_a?(Candidate)
      result = result.gsub("{{nome_do_candidato}}", record.name.to_s)
                    .gsub("{{email_do_candidato}}", record.email.to_s)
    elsif record.is_a?(User)
      result = result.gsub("{{nome_do_usuario}}", record.name.to_s)
                    .gsub("{{email_do_usuario}}", record.email.to_s)
    end

    result
  end

  def enqueue_delivery_jobs(message_ids, account_id:)
    return if message_ids.blank?
    jobs_to_enqueue = message_ids.map do |id|
      EmailWorker.new(id, account_id)
    end

    ActiveJob.perform_all_later(jobs_to_enqueue)
  end
end
