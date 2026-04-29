module V1
  module Users
    class AddressRelationshipsController < ApplicationController
      before_action :set_address_relationship, only: %i[show update destroy]

      def index
        perform_search(
          model: AddressRelationship,
          serializer: AddressRelationshipSerializer
        )
      end

      def show
        render_success(@address_relationship, serializer: AddressRelationshipSerializer)
      end

      def create
        @address_relationship = AddressRelationship.new(address_relationship_params.merge(account_id: @current_user.account_id))

        if @address_relationship.save
          return render_success(@address_relationship, serializer: AddressRelationshipSerializer, status: :created)
        end
        render_error(@address_relationship, status: :unprocessable_entity)
      end

      def update
        @address_relationship.update(address_relationship_params) ? render_success(@address_relationship, serializer: AddressRelationshipSerializer) : render_error(@address_relationship)
      end

      def destroy
        @address_relationship.update(is_deleted: true)
        render_success(@address_relationship, serializer: AddressRelationshipSerializer)
      end

      private

      def set_address_relationship
        @address_relationship = AddressRelationship.find(params[:id])
      end

      def address_relationship_params
        params.require(:address_relationship).permit(:reference_type, :reference_id, :is_deleted, :address_id, :account_id, :user_id)
      end
    end
  end
end
