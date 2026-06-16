class Experience < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :user, optional: true
  belongs_to :candidate
  belongs_to :occupation
  belongs_to :company
  belongs_to :city, optional: true

  attr_accessor :company_name, :occupation_name

  before_validation :find_or_create_company, if: :company_name?
  before_validation :find_or_create_occupation, if: :occupation_name?

  def role
    occupation&.name
  end


  def search_data
    {
      id: id,
      description: description,
      reasons_leaving: reasons_leaving,
      contract_type: contract_type,
      occupation_name: occupation&.name,
      company_name: company&.name,
      start_date: start_date,
      end_date: end_date,
      work_here: work_here,
      candidate_id: candidate_id,
      occupation_id: occupation_id,
      company_id: company_id,
      city_id: city_id,
      parse_language: parse_language,
      is_deleted: is_deleted,
      account_id: account_id,
      user_id: user_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  private

  def find_or_create_company
    return if company_name.blank?

    company = Company.find_by(
      "LOWER(name) = ? AND account_id = ? AND is_deleted = ?",
      company_name.downcase,
      account_id,
      false
    )

    unless company
      company = Company.create!(
        name: company_name.downcase,
        account_id: account_id,
        user_id: user_id
      )
    end

    self.company_id = company.id
  end

  def find_or_create_occupation
    return if occupation_name.blank?

    occupation = Occupation.find_by(
      "name = ? AND account_id = ? AND is_deleted = ?",
      occupation_name,
      account_id,
      false
    )

    unless occupation
      occupation = Occupation.create!(
        name: occupation_name,
        account_id: account_id,
        user_id: user_id
      )
    end

    self.occupation_id = occupation.id
  end

  def company_name?
    company_name.present?
  end

  def occupation_name?
    occupation_name.present?
  end
end
