# frozen_string_literal: true

class ApartmentService
  def self.create(name)
    return unless name

    Apartment::Tenant.create(name)
    # ApartmentService.remove_table(name)
    # ReindexService.call(name)
  end

  # def self.remove_table(tenant)
  #   unless tenant == 'public'
  #     Apartment.excluded_models.each do |model|
  #       ActiveRecord::Base.connection.execute("DROP TABLE IF EXISTS #{tenant}.#{model.downcase.pluralize} CASCADE")
  #     rescue ActiveRecord::StatementInvalid => e
  #       puts 'Moving foward from the following error:'
  #       puts e.message
  #     end
  #   end
  # end
end
