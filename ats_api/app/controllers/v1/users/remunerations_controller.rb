module V1
  module Users
    class RemunerationsController < ApplicationController
      before_action :set_remuneration, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        perform_search(
          model: Remuneration,
          serializer: RemunerationSerializer
        )
      end

      def show
        render_success(@remuneration, serializer: RemunerationSerializer)
      end

      def create
        @remuneration = Remuneration.create(remuneration_params.merge(
          account_id: @current_user.account_id,
          user_id: @current_user.id
        ))

        if @remuneration.save
          return render_success(@remuneration, serializer: RemunerationSerializer, status: :created)
        end
        render_error(@remuneration, status: :unprocessable_entity)
      end

      def update
        @remuneration.update(remuneration_params) ? render_success(@remuneration, serializer: RemunerationSerializer) : render_error(@remuneration)
      end

      def destroy
        @remuneration.update(is_deleted: true)
        @remuneration.save
        render_success(@remuneration, serializer: RemunerationSerializer)
      end

      private

      def set_remuneration
        @remuneration = Remuneration.find_by(id: params[:id])
        render_not_found("Remuneration") unless @remuneration
      end

      def ensure_owner
        return if @remuneration.user_id == @current_user.id
        render_simple_error("Não autorizado a realizar esta ação nesta remuneração", status: :forbidden)
      end

      def remuneration_params
        params.require(:remuneration).permit(:name, :description, :user_id, :account_id)
      end
    end
  end
end
