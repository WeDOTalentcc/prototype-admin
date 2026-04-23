module V1
  module Users
    class ListsController < V1::Users::ApplicationController
      before_action :set_list, only: %i[show update destroy]

      def index
        authorize List
        perform_search(
          model: List,
          serializer: ListSerializer,
          search_with_pin: search_with_pin.merge(where: { account_id: @current_user.account_id, is_deleted: false })
        )
      end

      def show
        authorize @list
        render_success(@list, serializer: ListSerializer)
      end

      def create
        authorize List
        @list = List.new(list_params.merge(
          user_id: @current_user.id,
          account_id: @current_user.account_id
        ))

        return render_success(@list, serializer: ListSerializer, status: :created) if @list.save

        render_error(@list, status: :unprocessable_entity)
      end

      def update
        authorize @list
        return render_success(@list, serializer: ListSerializer) if @list.update(list_params)

        render_error(@list)
      end

      def destroy
        authorize @list
        @list.update(is_deleted: true)
        render_success(@list, serializer: ListSerializer)
      end

      private

      def set_list
        @list = List.find_by(id: params[:id], account_id: @current_user.account_id)
        render_not_found("List") unless @list
      end

      def list_params
        params.require(:list).permit(:name, :is_public, :color, :description)
      end
    end
  end
end
