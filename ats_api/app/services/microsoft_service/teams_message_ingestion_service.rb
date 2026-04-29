# frozen_string_literal: true

module MicrosoftService
  class TeamsMessageIngestionService
    RECENT_MESSAGES_LIMIT = 5

    def self.call(subscription)
      new(subscription).call
    end

    def initialize(subscription)
      @subscription = subscription
    end

    def call
      unless api_user
        Rails.logger.warn "[TeamsMessageIngestion] No api_user with valid token for chat #{subscription.chat_id} (lia_user_id=#{subscription.lia_user_id}, recruiter_user_id=#{subscription.recruiter_user_id})"
        return
      end

      Rails.logger.info "[TeamsMessageIngestion] Fetching messages for chat #{subscription.chat_id} using user_id=#{api_user.id}"

      all_messages = fetch_recent_messages
      recruiter_messages = all_messages.select { |m| from_recruiter?(m) }

      Rails.logger.info "[TeamsMessageIngestion] Found #{all_messages.size} messages, #{recruiter_messages.size} from recruiter"

      recruiter_messages.each { |msg| store_message(msg) }
    rescue StandardError => e
      Rails.logger.error "[TeamsMessageIngestion] Failed for chat #{subscription.chat_id}: #{e.class} #{e.message}"
      Rails.logger.error e.backtrace&.first(5)&.join("\n")
    end

    private

    attr_reader :subscription

    def api_user
      @api_user ||= resolve_api_user
    end

    def lia_azure_id
      @lia_azure_id ||= resolve_lia_azure_id
    end

    def resolve_lia_azure_id
      cache_key = "lia_azure_id:#{subscription.lia_user_id}"
      Rails.cache.fetch(cache_key, expires_in: 1.hour) do
        me = MicrosoftService::Api.get("/me", api_user)
        me&.dig("id")
      end
    rescue StandardError => e
      Rails.logger.warn "[TeamsMessageIngestion] Failed to resolve Lia Azure ID: #{e.message}"
      nil
    end

    def resolve_api_user
      lia = User.find_by(id: subscription.lia_user_id)
      return lia if lia&.ms_access_token.present?

      recruiter = User.find_by(id: subscription.recruiter_user_id)
      return recruiter if recruiter&.ms_access_token.present?

      nil
    end

    def fetch_recent_messages
      response = MicrosoftService::Api.get(
        "/chats/#{subscription.chat_id}/messages",
        api_user,
        params: { "$top" => RECENT_MESSAGES_LIMIT, "$orderby" => "createdDateTime desc" }
      )

      response&.dig("value") || []
    end

    def from_recruiter?(teams_msg)
      sender_id = teams_msg.dig("from", "user", "id")
      return false if sender_id.blank?
      return false if lia_azure_id.blank?

      sender_id != lia_azure_id
    end

    def store_message(teams_msg)
      content = teams_msg.dig("body", "content")
      return if content.blank?

      persist_message(teams_msg, content)
    end

    def persist_message(teams_msg, content)
      recruiter = User.find_by(id: subscription.recruiter_user_id)
      return unless recruiter

      if already_stored?(recruiter, teams_msg["id"])
        Rails.logger.debug "[TeamsMessageIngestion] Skipping already stored message #{teams_msg['id']}"
        return
      end

      workspace = find_or_create_teams_workspace(recruiter)

      message = Message.create!(
        account_id: recruiter.account_id,
        reference: recruiter,
        parent_message: find_last_lia_message(recruiter),
        content: sanitize_html(content),
        entity: Message::ROLE_USER,
        status: Message::STATUS_NOT_ANSWERED,
        workspace_id: workspace.id,
        metadata: build_metadata(teams_msg)
      )

      Rails.logger.info "[TeamsMessageIngestion] Created Message##{message.id} from Teams (teams_msg_id=#{teams_msg['id']})"
    rescue StandardError => e
      Rails.logger.error "[TeamsMessageIngestion] Store failed: #{e.class} #{e.message}"
    end

    def already_stored?(recruiter, teams_message_id)
      Message.where(reference: recruiter)
             .where("metadata->>'teams_message_id' = ?", teams_message_id)
             .exists?
    end

    def find_last_lia_message(recruiter)
      Message.where(reference: recruiter, entity: Message::ROLE_SYSTEM)
             .order(created_at: :desc)
             .first
    end

    def build_metadata(teams_msg)
      {
        source: "teams",
        hub_mode: true,
        session_id: "teams_#{subscription.chat_id}",
        teams_message_id: teams_msg["id"],
        teams_chat_id: subscription.chat_id,
        teams_lia_user_id: subscription.lia_user_id,
        received_at: teams_msg["createdDateTime"]
      }
    end

    def find_or_create_teams_workspace(recruiter)
      Workspace.find_or_create_for_domain(
        user: recruiter,
        account: recruiter.account,
        domain: "teams",
        domain_reference_id: subscription.chat_id
      )
    end

    def sanitize_html(html_content)
      ActionController::Base.helpers.strip_tags(html_content).strip
    end
  end
end
