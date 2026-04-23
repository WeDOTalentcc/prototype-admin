# frozen_string_literal: true

class Sector < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :parent_sector, class_name: "Sector", optional: true
  has_many :child_sectors, class_name: "Sector", foreign_key: "parent_sector_id", dependent: :destroy
  belongs_to :account, optional: true

  # Validações
  validates :name, presence: true
  validates :level, presence: true, numericality: { only_integer: true, greater_than_or_equal_to: 0 }
  validate :validate_parent_level
  validate :validate_public_sector_has_no_account

  # Scopes
  scope :active, -> { where(is_deleted: false) }
  scope :public_sectors, -> { where(is_public: true, account_id: nil) }
  scope :for_account, ->(account_id) { where(account_id: account_id) }
  scope :root_sectors, -> { where(parent_sector_id: nil) }
  scope :by_level, ->(level) { where(level: level) }
  scope :with_children, -> { includes(:child_sectors) }
  scope :ordered, -> { order(level: :asc, name: :asc) }

  # Callbacks
  before_validation :set_level
  before_destroy :check_has_children

  def search_data
    {
      name: name,
      description: description,
      icon: icon,
      tags: tags,
      level: level,
      parent_sector_id: parent_sector_id,
      parent_sector_name: parent_sector&.name,
      is_public: is_public,
      is_deleted: is_deleted,
      account_id: account_id,
      has_children: child_sectors.any?
    }
  end

  def self.search_fields
    [ :name, :description, :tags ]
  end

  def self.include_base
    includes(:parent_sector, :child_sectors, :account)
  end

  def self.default_search_order
    { level: :asc, name: :asc }
  end

  # Métodos de instância
  def has_children?
    child_sectors.exists?
  end

  def children_count
    child_sectors.count
  end

  def full_path
    return name if parent_sector.nil?

    "#{parent_sector.full_path} > #{name}"
  end

  def ancestors
    return [] if parent_sector.nil?

    [ parent_sector ] + parent_sector.ancestors
  end

  def descendants
    child_sectors.flat_map { |child| [ child ] + child.descendants }
  end

  def siblings
    return Sector.none if parent_sector.nil?

    parent_sector.child_sectors.where.not(id: id)
  end

  # Seeds de dados padrão
  def self.create_default_sectors
    sectors_data = [
      {
        name: "Technology & Software",
        icon: "🖥️",
        level: 0,
        children: [
          { name: "Tecnologia da informação", tags: [ "B2B", "IT Services", "Cloud" ] },
          { name: "Software e desenvolvimento", tags: [ "SaaS", "B2B", "B2C", "API" ] },
          { name: "Serviços de internet", tags: [ "B2C", "B2B", "Online Media", "SaaS" ] },
          { name: "Segurança de redes e computadores", tags: [ "B2B", "Cybersecurity", "SaaS" ] },
          { name: "Telecomunicações", tags: [ "B2C", "B2B", "ISP", "5G" ] },
          { name: "Hardware e equipamentos", tags: [ "B2B", "B2C", "Hardware" ] },
          { name: "Semicondutores", tags: [ "B2B", "Hardware", "AI Chips" ] }
        ]
      },
      {
        name: "Financial Services",
        icon: "💰",
        level: 0,
        children: [
          { name: "Serviços financeiros", tags: [ "B2B", "B2C", "Payments", "Credit" ] },
          { name: "Banco de investimentos", tags: [ "B2C", "B2B", "Banking" ] },
          { name: "Seguros", tags: [ "B2C", "B2B", "Insurtech" ] },
          { name: "Capital de risco", tags: [ "B2B", "Investment", "Venture Capital" ] },
          { name: "Gestão de investimentos", tags: [ "B2B", "B2C", "Asset Management" ] },
          { name: "Fintech", tags: [ "Fintech", "B2C", "B2B", "SaaS" ] }
        ]
      },
      {
        name: "Healthcare & Pharma",
        icon: "🏥",
        level: 0,
        children: [
          { name: "Saúde e assistência médica", tags: [ "B2C", "B2B", "Health Care" ] },
          { name: "Farmacêutica", tags: [ "B2B", "Pharmaceuticals", "R&D" ] },
          { name: "Biotecnologia", tags: [ "B2B", "Biotechnology", "R&D" ] },
          { name: "Equipamentos médicos", tags: [ "B2B", "Medical Devices", "IoT" ] },
          { name: "Hospitais e clínicas", tags: [ "B2C", "Hospitals & Health Care" ] },
          { name: "Saúde mental e bem-estar", tags: [ "B2B2C", "B2C", "Wellness", "SaaS" ] }
        ]
      },
      {
        name: "Retail & E-commerce",
        icon: "🛒",
        level: 0,
        children: [
          { name: "Varejo", tags: [ "B2C", "Retail", "Omni-channel" ] },
          { name: "E-commerce", tags: [ "B2C", "B2B", "Marketplace", "D2C" ] },
          { name: "Bens de consumo", tags: [ "B2B", "B2C", "CPG" ] },
          { name: "Cosméticos e beleza", tags: [ "B2C", "D2C", "Retail", "Cosmetics" ] },
          { name: "Moda e acessórios", tags: [ "B2C", "Retail", "Apparel & Fashion" ] },
          { name: "Alimentos e bebidas", tags: [ "B2B", "B2C", "Food & Beverages" ] }
        ]
      },
      {
        name: "Industry, Construction & Manufacturing",
        icon: "🏭",
        level: 0,
        children: [
          { name: "Manufatura", tags: [ "B2B", "Industrial Automation" ] },
          { name: "Automotivo", tags: [ "B2B", "IoT", "Embedded Systems" ] },
          { name: "Químicos", tags: [ "B2B", "Chemicals", "Manufacturing" ] },
          { name: "Construção civil", tags: [ "B2B", "Construction", "PropTech" ] },
          { name: "Mineração", tags: [ "B2B", "Mining & Metals" ] },
          { name: "Papel e celulose", tags: [ "B2B", "Paper & Forest Products" ] },
          { name: "Imóveis e real estate", tags: [ "B2C", "B2B", "Real Estate", "Proptech" ] },
          { name: "Design e arquitetura", tags: [ "B2B", "Architecture & Planning" ] }
        ]
      },
      {
        name: "Energy & Utilities",
        icon: "⚡",
        level: 0,
        children: [
          { name: "Energia", tags: [ "B2B", "B2C", "Energy" ] },
          { name: "Petróleo e gás", tags: [ "B2B", "Oil & Energy" ] },
          { name: "Energias renováveis", tags: [ "B2B", "Renewables & Environment" ] },
          { name: "Utilidades públicas", tags: [ "B2C", "B2B", "Utilities" ] }
        ]
      },
      {
        name: "Transportation & Logistics",
        icon: "🚚",
        level: 0,
        children: [
          { name: "Logística e supply chain", tags: [ "B2B", "LogTech", "Last-Mile" ] },
          { name: "Aviação", tags: [ "B2C", "B2B", "Airlines" ] },
          { name: "Aeroespacial", tags: [ "B2B", "Aerospace & Defense" ] },
          { name: "Transporte marítimo", tags: [ "B2B", "Maritime", "Logistics" ] },
          { name: "Transporte rodoviário", tags: [ "B2C", "B2B", "Logistics" ] }
        ]
      },
      {
        name: "Media & Entertainment",
        icon: "🎬",
        level: 0,
        children: [
          { name: "Mídia e comunicação", tags: [ "B2C", "B2B", "Broadcast Media" ] },
          { name: "Mídia online", tags: [ "B2C", "B2B", "Online Media" ] },
          { name: "Entretenimento", tags: [ "B2C", "B2B", "Entertainment" ] },
          { name: "Publicidade e marketing", tags: [ "B2B", "AdTech", "MarTech" ] },
          { name: "Produção audiovisual", tags: [ "B2B", "Media Production" ] },
          { name: "Jogos eletrônicos", tags: [ "B2C", "Gaming", "Mobile" ] }
        ]
      },
      {
        name: "Education & Research",
        icon: "🎓",
        level: 0,
        children: [
          { name: "Educação", tags: [ "B2C", "B2B", "EdTech" ] },
          { name: "Pesquisa e desenvolvimento", tags: [ "B2B", "R&D" ] },
          { name: "Treinamento e capacitação", tags: [ "B2B", "B2C", "EdTech", "SaaS" ] }
        ]
      },
      {
        name: "Professional Services",
        icon: "💼",
        level: 0,
        children: [
          { name: "Consultoria estratégica", tags: [ "B2B", "Management Consulting" ] },
          { name: "Consultoria em TI", tags: [ "B2B", "IT Consulting" ] },
          { name: "Recursos humanos", tags: [ "SaaS", "B2B", "HR Tech" ] },
          { name: "Recrutamento e seleção", tags: [ "B2B", "Staffing & Recruiting" ] },
          { name: "Serviços jurídicos", tags: [ "B2B", "B2C", "LegalTech" ] },
          { name: "Contabilidade e auditoria", tags: [ "B2B", "Accounting" ] }
        ]
      },
      {
        name: "Agriculture & Food",
        icon: "🌾",
        level: 0,
        children: [
          { name: "Agronegócio", tags: [ "B2B", "AgTech", "IoT" ] },
          { name: "Agricultura", tags: [ "B2B", "AgTech" ] },
          { name: "Pecuária", tags: [ "B2B", "Livestock" ] },
          { name: "Processamento de alimentos", tags: [ "B2B", "B2C", "Food Production" ] }
        ]
      },
      {
        name: "Tourism & Hospitality",
        icon: "✈️",
        level: 0,
        children: [
          { name: "Turismo e hotelaria", tags: [ "B2C", "B2B", "Travel" ] },
          { name: "Restaurantes e alimentação", tags: [ "B2C", "B2B", "Food Service" ] },
          { name: "Eventos e entretenimento", tags: [ "B2C", "B2B", "Events" ] }
        ]
      },
      {
        name: "Government & Non-Profit",
        icon: "🏛️",
        level: 0,
        children: [
          { name: "Governo e administração pública", tags: [ "Public Sector", "GovTech" ] },
          { name: "Organizações sem fins lucrativos", tags: [ "Non-Profit", "NGO" ] },
          { name: "Think tanks", tags: [ "Research", "Public Policy" ] }
        ]
      },
      {
        name: "Other",
        icon: "📦",
        level: 0,
        children: [
          { name: "Outros", tags: [ "N/A" ] }
        ]
      }
    ]

    transaction do
      sectors_data.each do |group_data|
        parent = Sector.create!(
          name: group_data[:name],
          icon: group_data[:icon],
          level: group_data[:level],
          is_public: true,
          account_id: nil
        )

        group_data[:children].each do |child_data|
          parent.child_sectors.create!(
            name: child_data[:name],
            tags: child_data[:tags],
            level: 1,
            is_public: true,
            account_id: nil
          )
        end
      end
    end
  end

  private

  def set_level
    self.level = parent_sector ? parent_sector.level + 1 : 0
  end

  def validate_parent_level
    return if parent_sector.nil?

    if parent_sector.level >= level
      errors.add(:parent_sector, "deve ter um nível inferior ao nível atual")
    end
  end

  def validate_public_sector_has_no_account
    if is_public && account_id.present?
      errors.add(:account_id, "setores públicos não podem ter account_id")
    end

    if !is_public && account_id.nil?
      errors.add(:account_id, "setores privados devem ter account_id")
    end
  end

  def check_has_children
    if has_children?
      errors.add(:base, "Não é possível excluir um setor que possui subsetores")
      throw :abort
    end
  end
end
