module V1
  module Users
    class AddressesController < ApplicationController
      before_action :set_address, only: %i[show update destroy]

      def index
        perform_search(
          model: Address,
          serializer: AddressSerializer
        )
      end

      def show
        render_success(@address, serializer: AddressSerializer)
      end

      def create
        @address = Address.new(set_address_params.merge(account_id: @current_user.account_id))

        if @address.save
          return render_success(@address, serializer: AddressSerializer, status: :created)
        end
        render_error(@address, status: :unprocessable_entity)
      end

      def update
        @address.update(set_address_params) ? render_success(@address, serializer: AddressSerializer) : render_error(@address)
      end

      def destroy
        @address.update(is_deleted: true)
        render_success(@address, serializer: AddressSerializer)
      end

      def relationships
        entity = params[:entity]
        id = params[:id]
        return render_error("Entity not found", status: :not_found) unless entity && id

        relationships = AddressRelationship.where(reference_type: entity, reference_id: id).pluck(:address_id)
        addresses = Address.where(id: relationships)

        params[:where] ||= {}
        params[:where][:id] = addresses.pluck(:id)

        perform_search(
          model: Address,
          serializer: AddressSerializer
        )
      end

      private

      def set_address
        @address = Address.find(params[:id])
      end

      def set_address_params
        address = address_params
        city = City.find_by(id: address[:city_id]) if address[:city_id].present?
        address[:state_id] = city&.state_id if city
        address[:country_id] = city&.country_id if city
        address
      end

      def address_params
        params.require(:address).permit(:street, :number, :complement, :neighborhood, :zip_code,
                                        :city_id, :state_id, :country_id, :title, :address_type, :description,
                                        :worksite, :bill_to, :sold_to)
      end
    end
  end
end
