module V1
  module Users
    class ApproversController < ApplicationController
      before_action :set_approver, only: %i[show update destroy]

      def index
        params[:where] = (params[:where] || {}).merge(account_id: @current_user.account_id)
        params[:where][:is_deleted] ||= false

        perform_search(model: Approver, serializer: ApproverSerializer, include_aggregators: true)
      end

      def show
        render_success(@approver, serializer: ApproverSerializer)
      end

      def create
        approver = Approver.new(approver_params)
        approver.account_id = @current_user.account_id
        approver.name ||= approver.user&.name
        approver.email ||= approver.user&.email

        return render_error(approver) unless approver.save

        render_success(approver, serializer: ApproverSerializer, status: :created)
      end

      def update
        return render_error(@approver) unless @approver.update(approver_params)

        render_success(@approver, serializer: ApproverSerializer)
      end

      def destroy
        @approver.update(is_deleted: true)
        render_success(@approver, serializer: ApproverSerializer)
      end

      def reorder
        return render json: { error: "items required" }, status: :unprocessable_entity if params[:items].blank?

        Approver.transaction do
          params[:items].each_with_index do |item, idx|
            account_approvers.where(id: item[:id]).update_all(approval_level: idx + 1)
          end
        end
        render json: { message: "Ordem atualizada" }, status: :ok
      end

      def by_type
        type = params[:type]
        return render json: { error: "type required" }, status: :unprocessable_entity if type.blank?

        approvers = account_approvers.active.by_type(type).ordered.includes(:user, :department)
        render_success(approvers, serializer: ApproverSerializer)
      end

      APPROVAL_TYPE_LABELS = { "job" => "Vaga", "hiring" => "Contratação", "offer" => "Oferta" }.freeze

      def approval_types
        types = Approver::APPROVAL_TYPES.map { |type| { id: type, name: APPROVAL_TYPE_LABELS[type] } }
        render json: { data: types }
      end

      private

      def account_approvers
        Approver.where(account_id: @current_user.account_id)
      end

      def set_approver
        @approver = account_approvers.find_by(id: params[:id])
        render_not_found("Aprovador") unless @approver
      end

      def approver_params
        params.require(:approver).permit(
          :user_id, :department_id, :approval_type, :approval_level,
          :limit_value, :name, :email, :title, :is_active
        )
      end
    end
  end
end
