# frozen_string_literal: true

module MicrosoftService
  class Teams
    class Error < StandardError
      attr_reader :code

      def initialize(message, code: nil)
        @code = code
        super(message)
      end
    end

    VALID_CONTENT_TYPES = %w[html text].freeze
    GRAPH_USERS_BIND = "https://graph.microsoft.com/v1.0/users('%s')"

    def self.send_message(user:, content:, content_type: "html", chat_id: nil, to: nil,
                          team_id: nil, channel_id: nil, team_name: nil, channel_name: nil,
                          attachments: nil)
      raise Error.new("Content is required", code: "empty_content") if content.to_s.strip.empty?

      target = resolve_target(
        user: user, chat_id: chat_id, to: to,
        team_id: team_id, channel_id: channel_id,
        team_name: team_name, channel_name: channel_name
      )

      path = build_message_path(target)
      body = build_message_body(content, content_type, attachments)

      response = MicrosoftService::Api.post(path, user, body: body)
      raise Error.new("Failed to send Teams message", code: "provider_error") if response.nil?

      { message_id: response["id"], chat_id: target[:chat_id] }
    rescue Error
      raise
    rescue StandardError => e
      Rails.logger.error("[Teams] send_message error: #{e.class} #{e.message}")
      raise Error.new(e.message, code: "unexpected_error")
    end

    def self.resolve_target(user:, chat_id:, to:, team_id:, channel_id:, team_name:, channel_name:)
      return { type: :chat, chat_id: chat_id } if chat_id.to_s.present?
      return { type: :channel, team_id: team_id, channel_id: channel_id } if team_id.to_s.present? && channel_id.to_s.present?
      return resolve_direct_message(user, to.to_s) if to.to_s.present?
      return resolve_team_channel(user, team_name.to_s, channel_name.to_s) if team_name.to_s.present? && channel_name.to_s.present?

      raise Error.new("Provide chat_id, team_id + channel_id, to, or team_name + channel_name", code: "invalid_target")
    end
    private_class_method :resolve_target

    def self.resolve_direct_message(user, target_email)
      resolved = ensure_one_on_one_chat(user, target_email)
      raise Error.new("Cannot send DM to yourself", code: "self_dm") if resolved == :self
      raise Error.new("Could not resolve or create chat for recipient", code: "unresolved_target") if resolved.to_s.empty?

      { type: :chat, chat_id: resolved }
    end
    private_class_method :resolve_direct_message

    def self.resolve_team_channel(user, team_name, channel_name)
      pair = find_team_and_channel_ids(user, team_name, channel_name)
      raise Error.new("Team or channel not found", code: "team_or_channel_not_found") if pair.nil?

      { type: :channel, team_id: pair[:team_id], channel_id: pair[:channel_id] }
    end
    private_class_method :resolve_team_channel

    def self.build_message_path(target)
      return "/chats/#{target[:chat_id]}/messages" if target[:type] == :chat

      raise Error.new("Invalid target", code: "invalid_target") if target[:team_id].to_s.empty? || target[:channel_id].to_s.empty?

      "/teams/#{target[:team_id]}/channels/#{target[:channel_id]}/messages"
    end
    private_class_method :build_message_path

    def self.build_message_body(content, content_type, attachments = nil)
      ct = VALID_CONTENT_TYPES.include?(content_type.to_s.downcase) ? content_type.to_s.downcase : "html"
      body = { body: { contentType: ct, content: content.to_s } }
      body[:attachments] = attachments if attachments.present?
      body
    end
    private_class_method :build_message_body

    def self.ensure_one_on_one_chat(user, target_email)
      me = MicrosoftService::Api.get("/me", user)
      me_id = me&.dig("id")
      return nil if me_id.to_s.empty?

      me_upn = (me["userPrincipalName"] || me["mail"]).to_s.downcase
      return :self if me_upn.present? && me_upn == target_email.downcase

      create_one_on_one_chat(user, me_id, target_email)
    end
    private_class_method :ensure_one_on_one_chat

    def self.create_one_on_one_chat(user, me_id, target_email)
      body = {
        "chatType" => "oneOnOne",
        "members" => [
          build_chat_member(me_id),
          build_chat_member(target_email)
        ]
      }

      response = MicrosoftService::Api.post("/chats", user, body: body)
      response&.dig("id")
    rescue StandardError => e
      Rails.logger.error("[Teams] create_one_on_one_chat error: #{e.class} #{e.message}")
      nil
    end
    private_class_method :create_one_on_one_chat

    def self.build_chat_member(user_identifier)
      {
        "@odata.type" => "#microsoft.graph.aadUserConversationMember",
        "roles" => [ "owner" ],
        "user@odata.bind" => format(GRAPH_USERS_BIND, user_identifier)
      }
    end
    private_class_method :build_chat_member

    def self.find_team_and_channel_ids(user, team_name, channel_name)
      teams = MicrosoftService::Api.get("/me/joinedTeams", user)
      team = find_by_display_name(teams, team_name)
      return unless team

      channels = MicrosoftService::Api.get("/teams/#{team['id']}/channels", user)
      channel = find_by_display_name(channels, channel_name)
      return unless channel

      { team_id: team["id"], channel_id: channel["id"] }
    end
    private_class_method :find_team_and_channel_ids

    def self.find_by_display_name(response, name)
      items = response&.dig("value")
      return unless items.is_a?(Array)

      items.find { |item| item["displayName"].to_s.casecmp?(name.to_s) }
    end
    private_class_method :find_by_display_name
  end
end
