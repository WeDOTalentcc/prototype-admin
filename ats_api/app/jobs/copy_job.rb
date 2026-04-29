module CopyJob
  class Copy < ApplicationJob
    queue_as :default
    sidekiq_options retry: false

    def perform(record_class_name, record_id, class_relationships, attributes_overwrite, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        class_to_copy = record_class_name.constantize.find(record_id)
        class_copy = class_to_copy.dup
        overwrite_attributes(attributes_overwrite, class_copy)

        class_copy.save
        class_name = class_to_copy.class.name.underscore

        class_relationships.each do |relationship|
          reference_name = "#{class_name}_id"
          relationship_class = relationship.constantize

          if relationship_class.attribute_names.include?(reference_name)
            make_relationships(class_to_copy, class_copy, relationship_class, reference_name)
            next
          end

          make_polymorphic_relationships(class_to_copy, class_copy, relationship_class)
        end

        class_copy.try(:reindex)
      end
    end

    def make_polymorphic_relationships(class_to_copy, class_copy, class_relationships)
      class_relationships.where(reference_type: class_to_copy.class.name, reference_id: class_to_copy.id).each do |object|
        object_to_copy = object.dup
        object_to_copy[:reference_id] = class_copy.id
        object_to_copy.save
        object_to_copy.try(:reindex)
      end
    end

    def make_relationships(class_to_copy, class_copy, class_relationships, reference_name)
      class_relationships.where("#{reference_name} = ?", class_to_copy.id).each do |object|
        object_to_copy = object.dup
        object_to_copy[reference_name.to_sym] = class_copy.id
        object_to_copy.save
        object_to_copy.try(:reindex)
      end
    end

    def overwrite_attributes(attributes_overwrite, class_copy)
      attributes_overwrite.each do |attribute|
        attribute_name = attribute[0]
        attribute_value = attribute[1]
        class_copy[attribute_name.to_sym] = attribute_value
      end
    end
  end
end
