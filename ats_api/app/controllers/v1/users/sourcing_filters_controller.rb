module V1
  module Users
    class SourcingFiltersController < V1::Users::ApplicationController
      before_action :set_sourcing_filter, only: %i[destroy]

      def index
        authorize SourcingFilter
        filters = SourcingFilter.by_account(@current_user.account_id).active.recently_used
        render_success(filters, serializer: SourcingFilterSerializer)
      end

      def create
        authorize SourcingFilter
        @sourcing_filter = SourcingFilter.new(sourcing_filter_params.merge(
          user_id: @current_user.id,
          account_id: @current_user.account_id
        ))

        return render_success(@sourcing_filter, serializer: SourcingFilterSerializer, status: :created) if @sourcing_filter.save

        render_error(@sourcing_filter, status: :unprocessable_entity)
      end

      def destroy
        authorize @sourcing_filter
        @sourcing_filter.update(is_deleted: true)
        render_success(@sourcing_filter, serializer: SourcingFilterSerializer)
      end

      private

      def set_sourcing_filter
        @sourcing_filter = SourcingFilter.find_by(id: params[:id], account_id: @current_user.account_id)
        render_not_found("SourcingFilter") unless @sourcing_filter
      end

      def sourcing_filter_params
        params.require(:sourcing_filter).permit(:name, parameters: {})
      end
    end
  end
end
