# frozen_string_literal: true

class EmailTemplateSerializer
  include JSONAPI::Serializer

  attributes :id,
             :name,
             :subject,
             :content,
             :category_id,
             :account_id,
             :user_id,
             :is_deleted,
             :is_automated,
             :delay_hours,
             :response_deadline_days,
             :trigger_event,
             :created_at,
             :updated_at

  attribute :user do |email_template|
    next unless email_template.user

    {
      id: email_template.user.id,
      name: email_template.user.name,
      email: email_template.user.email
    }
  end

  attribute :account do |email_template|
    next unless email_template.account

    {
      id: email_template.account.id,
      name: email_template.account.name
    }
  end

  attribute :category do |email_template|
    next unless email_template.category_id

    EmailTemplate::CATEGORIES.find { |c| c[:id] == email_template.category_id }&.dig(:name)
  end

  attribute :category_color do |email_template|
    next unless email_template.category_id

    EmailTemplate::CATEGORIES.find { |c| c[:id] == email_template.category_id }&.dig(:color)
  end
end
