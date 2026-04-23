# frozen_string_literal: true

require "csv"

module Jobs
  class ExportService
    FORMATS = %w[csv pdf].freeze

    def initialize(job:, format: "csv")
      @job = job
      @format = format.to_s.downcase
    end

    def call
      return error("Formato inválido. Use: #{FORMATS.join(', ')}") unless FORMATS.include?(format)

      preload_data
      analytics = fetch_analytics

      case format
      when "csv" then generate_csv(analytics)
      when "pdf" then generate_pdf(analytics)
      end
    end

    private

    attr_reader :job, :format

    def preload_data
      @skills = job.skills.to_a
      @benefits = job.benefits.to_a
      @languages = job.languages.to_a
      @remunerations = job.remuneration_relationships.includes(:remuneration).where(is_deleted: false).to_a
      @selective_processes = job.selective_processes.where(is_deleted: false).order(:position).to_a
      @company = job.company
    end

    def fetch_analytics
      ::Jobs::AnalyticsService.new(job: job).call
    rescue StandardError
      nil
    end

    def generate_csv(analytics)
      content = CSV.generate(headers: true, col_sep: ";") do |csv|
        csv << [ "Relatório da Vaga - #{job.title}" ]
        csv << []

        csv << [ "INFORMAÇÕES BÁSICAS" ]
        basic_fields.each { |label, value| csv << [ label, value ] }
        csv << []

        csv << [ "LOCALIZAÇÃO" ]
        location_fields.each { |label, value| csv << [ label, value ] }
        csv << []

        csv << [ "REMUNERAÇÃO" ]
        @remunerations.each do |rr|
          csv << [ rr.remuneration&.name, "#{rr.currency} #{rr.value}" ]
        end
        csv << []

        csv << [ "HABILIDADES" ]
        @skills.each { |s| csv << [ s.name ] }
        csv << []

        csv << [ "BENEFÍCIOS" ]
        @benefits.each { |b| csv << [ b.name, b.try(:category) ] }
        csv << []

        csv << [ "IDIOMAS" ]
        @languages.each { |l| csv << [ l.name ] }
        csv << []

        csv << [ "ETAPAS DO PROCESSO" ]
        @selective_processes.each do |sp|
          csv << [ sp.name, sp.status, "Posição: #{sp.position}" ]
        end
        csv << []

        if analytics
          csv << [ "ANALYTICS" ]
          overview = analytics[:overview] || {}
          csv << [ "Total de candidaturas", overview[:total_applies] ]
          csv << [ "Dias desde publicação", overview[:days_since_published] ]
          csv << [ "Dias até deadline", overview[:days_until_deadline] ]

          funnel = analytics[:funnel] || {}
          csv << [ "Taxa de conversão geral", "#{funnel[:overall_conversion_rate]}%" ]
          csv << [ "Gargalo", funnel[:bottleneck_stage] ]
          csv << [ "Tempo médio no pipeline (dias)", funnel[:avg_total_pipeline_days] ]
        end
      end

      { success: true, content: content, filename: "vaga_#{job.id}_#{Date.current}.csv", content_type: "text/csv" }
    end

    def generate_pdf(analytics)
      pdf = Prawn::Document.new(page_size: "A4", margin: 40)

      add_header(pdf)
      add_basic_info(pdf)
      add_location(pdf)
      add_remunerations(pdf)
      add_skills_and_benefits(pdf)
      add_selective_processes(pdf)
      add_analytics(pdf, analytics) if analytics

      {
        success: true,
        content: pdf.render,
        filename: "vaga_#{job.id}_#{Date.current}.pdf",
        content_type: "application/pdf"
      }
    end

    def add_header(pdf)
      if @company&.logo.present?
        begin
          logo = URI.parse(@company.logo).open
          pdf.image logo, at: [ pdf.bounds.right - 100, pdf.cursor ], width: 80
        rescue StandardError
          # logo unavailable
        end
      end

      pdf.text job.title, size: 20, style: :bold
      pdf.text "Gerado em #{Date.current.strftime('%d/%m/%Y')}", size: 10, color: "666666"
      pdf.move_down 20
    end

    def add_basic_info(pdf)
      pdf.text "Informações Básicas", size: 14, style: :bold
      pdf.move_down 5

      basic_fields.each do |label, value|
        pdf.text "#{label}: #{value}", size: 10
      end
      pdf.move_down 15
    end

    def add_location(pdf)
      pdf.text "Localização", size: 14, style: :bold
      pdf.move_down 5

      location_fields.each do |label, value|
        pdf.text "#{label}: #{value}", size: 10
      end
      pdf.move_down 15
    end

    def add_remunerations(pdf)
      return if @remunerations.empty?

      pdf.text "Remuneração", size: 14, style: :bold
      pdf.move_down 5

      data = @remunerations.map { |rr| [ rr.remuneration&.name, "#{rr.currency} #{rr.value}" ] }
      pdf.table([ [ "Tipo", "Valor" ] ] + data, width: pdf.bounds.width, cell_style: { size: 9 })
      pdf.move_down 15
    end

    def add_skills_and_benefits(pdf)
      unless @skills.empty?
        pdf.text "Habilidades", size: 14, style: :bold
        pdf.move_down 5
        pdf.text @skills.map(&:name).join(", "), size: 10
        pdf.move_down 15
      end

      unless @benefits.empty?
        pdf.text "Benefícios", size: 14, style: :bold
        pdf.move_down 5
        pdf.text @benefits.map(&:name).join(", "), size: 10
        pdf.move_down 15
      end
    end

    def add_selective_processes(pdf)
      return if @selective_processes.empty?

      pdf.text "Etapas do Processo", size: 14, style: :bold
      pdf.move_down 5

      data = @selective_processes.map { |sp| [ sp.position, sp.name, sp.status ] }
      pdf.table([ [ "#", "Etapa", "Status" ] ] + data, width: pdf.bounds.width, cell_style: { size: 9 })
      pdf.move_down 15
    end

    def add_analytics(pdf, analytics)
      pdf.start_new_page

      pdf.text "Analytics", size: 16, style: :bold
      pdf.move_down 10

      overview = analytics[:overview] || {}
      data = [
        [ "Métrica", "Valor" ],
        [ "Total de candidaturas", overview[:total_applies].to_s ],
        [ "Dias desde publicação", overview[:days_since_published].to_s ],
        [ "Dias até deadline", overview[:days_until_deadline].to_s ]
      ]

      funnel = analytics[:funnel] || {}
      data << [ "Taxa de conversão geral", "#{funnel[:overall_conversion_rate]}%" ]
      data << [ "Gargalo", funnel[:bottleneck_stage].to_s ]
      data << [ "Tempo médio no pipeline (dias)", funnel[:avg_total_pipeline_days].to_s ]

      pdf.table(data, width: pdf.bounds.width, cell_style: { size: 9 })
    end

    def basic_fields
      seniority_text = job.seniority ? (Job::SENIORITY[job.seniority] || "N/A") : "N/A"
      employment_text = job.employment_type ? (Job::EMPLOYMENT_TYPES[job.employment_type] || "N/A") : "N/A"
      status_name = job.job_status&.name || "Sem status"

      [
        [ "ID", job.id ],
        [ "Título", job.title ],
        [ "Descrição", job.description&.truncate(500) ],
        [ "Status", status_name ],
        [ "Senioridade", seniority_text ],
        [ "Tipo de contrato", employment_text ],
        [ "Prioridade", Job::PRIORITY.find { |p| p["id"] == job.priority }&.dig("name") || "N/A" ],
        [ "Data de publicação", job.published_date&.strftime("%d/%m/%Y") ],
        [ "Deadline", job.application_deadline&.strftime("%d/%m/%Y") ],
        [ "Criado em", job.created_at&.strftime("%d/%m/%Y") ],
        [ "Atualizado em", job.updated_at&.strftime("%d/%m/%Y") ]
      ]
    end

    def location_fields
      wt = Job::WORKPLACE_TYPES.find { |w| w["id"].to_s == job.workplace_type.to_s }&.dig("name") || "N/A"

      [
        [ "Cidade", job.city || "N/A" ],
        [ "Estado", job.state || "N/A" ],
        [ "País", job.country || "N/A" ],
        [ "Regime", wt ]
      ]
    end

    def error(message)
      { success: false, error: message }
    end
  end
end
