# frozen_string_literal: true

module Microsoft
  class TeamsResponseJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 3

    ADAPTIVE_CARD_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"
    TABLE_LINE_PATTERN = /\|.*\|/
    SEPARATOR_PATTERN = /^\s*\|[\s\-:|]+\|\s*$/
    HEADING_PATTERN = /^\*\*|^#+\s/

    def perform(message_id, tenant, teams_origin = nil)
      Apartment::Tenant.switch!(tenant)

      @message = Message.find(message_id)
      @teams_chat_id, lia_user_id = resolve_teams_context(teams_origin)
      return if @teams_chat_id.blank? || lia_user_id.blank?

      @lia_user = User.find_by(id: lia_user_id)
      return unless @lia_user&.ms_access_token.present?

      @raw_content = extract_text_content
      return if @raw_content.blank?

      dispatch_message
      Rails.logger.info "[TeamsResponseJob] Sent Message##{message_id} to Teams chat #{@teams_chat_id}"
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.error "[TeamsResponseJob] Message not found: #{e.message}"
    rescue MicrosoftService::Teams::Error => e
      Rails.logger.error "[TeamsResponseJob] Teams send failed: #{e.message} (code: #{e.code})"
      raise if e.code == "unexpected_error"
    rescue StandardError => e
      Rails.logger.error "[TeamsResponseJob] Error: #{e.class} #{e.message}"
    end

    private

    def extract_text_content
      Nokogiri::HTML.fragment(@message.content.to_s).text.strip
    end

    def resolve_teams_context(teams_origin)
      return [ teams_origin["teams_chat_id"], teams_origin["teams_lia_user_id"] ] if teams_origin.is_a?(Hash)

      meta = @message.metadata
      return [ nil, nil ] unless meta.is_a?(Hash)

      [ meta["teams_chat_id"], meta["teams_lia_user_id"] ]
    end

    def dispatch_message
      agent_cards = message_metadata["cards"]
      return send_with_cards(agent_cards) if agent_cards.present?
      return send_with_adaptive_table if ascii_table?

      send_html
    end

    def message_metadata
      @message.metadata.is_a?(Hash) ? @message.metadata : {}
    end

    def send_with_cards(cards)
      attachments = cards.each_with_index.map { |card, i| build_card_attachment("card-#{i}", card) }
      refs = attachments.map { |a| "<attachment id=\"#{a[:id]}\"></attachment>" }.join
      body_content = "#{ERB::Util.html_escape(@raw_content.lines.first.to_s.strip)}<br/>#{refs}"

      send_to_teams(content: body_content, content_type: "html", attachments: attachments)
    end

    def send_with_adaptive_table
      sections = parse_sections(@raw_content)
      card_body = build_card_body(sections)

      attachment = build_adaptive_card_attachment("table-card", card_body)
      first_line = sections.find { |s| s[:type] == :text }&.dig(:lines)&.first || ""
      body_html = "#{ERB::Util.html_escape(first_line)}<br/><attachment id=\"table-card\"></attachment>"

      send_to_teams(content: body_html, content_type: "html", attachments: [ attachment ])
    end

    def send_html
      send_to_teams(content: @raw_content.gsub("\n", "<br/>"), content_type: "html")
    end

    def send_to_teams(content:, content_type:, attachments: nil)
      MicrosoftService::Teams.send_message(
        user: @lia_user,
        content: content,
        content_type: content_type,
        chat_id: @teams_chat_id,
        attachments: attachments
      )
    end

    def build_card_attachment(id, card)
      card_content = card["content"]
      {
        id: id,
        contentType: ADAPTIVE_CARD_CONTENT_TYPE,
        contentUrl: nil,
        content: card_content.is_a?(String) ? card_content : card_content.to_json
      }
    end

    def build_adaptive_card_attachment(id, body)
      {
        id: id,
        contentType: ADAPTIVE_CARD_CONTENT_TYPE,
        contentUrl: nil,
        content: { type: "AdaptiveCard", version: "1.5", body: body }.to_json
      }
    end

    def ascii_table?
      @raw_content.lines.count { |l| l.match?(TABLE_LINE_PATTERN) } >= 2
    end

    def parse_sections(text)
      sections = []
      current_text = []
      current_table = []

      text.lines.map(&:rstrip).each do |line|
        if line.match?(TABLE_LINE_PATTERN)
          flush_section(sections, :text, current_text) && current_text = []
          current_table << line
        else
          flush_section(sections, :table, current_table) && current_table = []
          current_text << line if line.present?
        end
      end

      flush_section(sections, :text, current_text)
      flush_section(sections, :table, current_table)
      sections
    end

    def flush_section(sections, type, lines)
      return false if lines.empty?

      sections << { type: type, lines: lines.dup }
      true
    end

    def build_card_body(sections)
      sections.flat_map { |section| render_section(section) }
    end

    def render_section(section)
      return [ build_adaptive_table(section[:lines]) ] if section[:type] == :table

      section[:lines].filter_map { |line| build_text_block(line) }
    end

    def build_text_block(line)
      weight = line.match?(HEADING_PATTERN) ? "bolder" : "default"
      clean = line.gsub(/^\*\*|\*\*$|^#+\s*/, "").strip
      return if clean.blank?

      {
        type: "TextBlock",
        text: clean,
        weight: weight,
        size: weight == "bolder" ? "medium" : "default",
        wrap: true
      }
    end

    def build_adaptive_table(lines)
      rows = lines.reject { |l| l.match?(SEPARATOR_PATTERN) }
                  .map { |l| l.strip.gsub(/^\||\|$/, "").split("|").map(&:strip) }

      return { type: "TextBlock", text: lines.join("\n"), wrap: true } if rows.empty?

      col_count = rows.map(&:size).max || 1

      {
        type: "Table",
        gridStyle: "accent",
        firstRowAsHeader: true,
        columns: col_count.times.map { { width: 1 } },
        rows: rows.each_with_index.map { |cells, idx| build_table_row(cells, col_count, header: idx.zero?) }
      }
    end

    def build_table_row(cells, col_count, header: false)
      padded = cells + Array.new([ col_count - cells.size, 0 ].max, "")

      {
        type: "TableRow",
        cells: padded.map do |cell|
          {
            type: "TableCell",
            items: [ {
              type: "TextBlock",
              text: cell,
              weight: header ? "bolder" : "default",
              size: "small",
              wrap: true
            } ]
          }
        end
      }
    end
  end
end
