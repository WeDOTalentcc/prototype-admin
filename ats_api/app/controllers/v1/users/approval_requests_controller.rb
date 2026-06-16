module V1
  module Users
    class ApprovalRequestsController < ApplicationController
      before_action :set_approval_request, only: %i[show approve reject cancel]

      def index
        params[:where] = (params[:where] || {}).merge(account_id: @current_user.account_id)
        params[:where][:is_deleted] ||= false

        perform_search(model: ApprovalRequest, serializer: ApprovalRequestSerializer, include_aggregators: true)
      end

      def show
        render_success(@approval_request, serializer: ApprovalRequestSerializer)
      end

      def create
        approval_request = ApprovalRequest.new(approval_request_params)
        approval_request.account_id = @current_user.account_id
        approval_request.requested_by = @current_user

        return render_error(approval_request) unless approval_request.save

        render_success(approval_request, serializer: ApprovalRequestSerializer, status: :created)
      end

      def approve
        return render json: { error: "Solicitação não está pendente" }, status: :unprocessable_entity unless @approval_request.pending?

        @approval_request.approve!(user: @current_user, comments: params[:comments])
        check_approval_chain

        render_success(@approval_request.reload, serializer: ApprovalRequestSerializer)
      end

      def reject
        return render json: { error: "Solicitação não está pendente" }, status: :unprocessable_entity unless @approval_request.pending?

        @approval_request.reject!(user: @current_user, comments: params[:comments])
        update_reference_status(:rejected)

        render_success(@approval_request.reload, serializer: ApprovalRequestSerializer)
      end

      def cancel
        return render json: { error: "Solicitação não está pendente" }, status: :unprocessable_entity unless @approval_request.pending?

        @approval_request.update(status: :cancelled)
        render_success(@approval_request.reload, serializer: ApprovalRequestSerializer)
      end

      def pending
        requests = account_requests.pending_approval.where(approver: user_approvers).includes(:approver, :requested_by).ordered

        if params[:job_id].present?
          apply_ids = Apply.where(job_id: params[:job_id], is_deleted: false).select(:id)
          requests = requests.where(reference_type: "Apply", reference_id: apply_ids)
        end

        render_success(requests, serializer: ApprovalRequestSerializer)
      end

      def my_requests
        requests = account_requests.where(requested_by: @current_user).includes(:approver, :approved_by).ordered
        render_success(requests, serializer: ApprovalRequestSerializer)
      end

      def by_reference
        return render json: { error: "reference_type e reference_id required" }, status: :unprocessable_entity if params[:reference_type].blank? || params[:reference_id].blank?

        requests = account_requests
                   .by_reference(params[:reference_type], params[:reference_id])
                   .includes(:approver, :requested_by, :approved_by)
                   .ordered
        render_success(requests, serializer: ApprovalRequestSerializer)
      end

      def create_chain
        reference = find_reference
        return render json: { error: "Referência não encontrada" }, status: :not_found unless reference

        requests = ApprovalRequest.create_approval_chain(
          account: @current_user.account,
          reference: reference,
          approval_type: params[:approval_type],
          requested_by: @current_user,
          department_id: params[:department_id]
        )

        return render json: { error: "Nenhum aprovador configurado" }, status: :unprocessable_entity if requests.empty?

        render json: { data: requests.map { |r| ApprovalRequestSerializer.new(r).serializable_hash[:data][:attributes] }, message: "Cadeia de aprovação criada" }, status: :created
      end

      private

      def account_requests
        ApprovalRequest.where(account_id: @current_user.account_id, is_deleted: false)
      end

      def user_approvers
        Approver.active.where(account_id: @current_user.account_id, user_id: @current_user.id)
      end

      def set_approval_request
        @approval_request = account_requests.find_by(id: params[:id])
        render_not_found("Solicitação de aprovação") unless @approval_request
      end

      def approval_request_params
        params.require(:approval_request).permit(
          :approver_id, :reference_type, :reference_id, :approval_level, :comments, :expires_at
        )
      end

      def find_reference
        return unless params[:reference_type].present? && params[:reference_id].present?

        klass = params[:reference_type].safe_constantize
        return unless klass

        klass.find_by(id: params[:reference_id], account_id: @current_user.account_id)
      end

      def check_approval_chain
        return unless @approval_request.all_approved_for_reference?

        update_reference_status(:approved)
      end

      def update_reference_status(status)
        reference = @approval_request.reference
        return unless reference

        case @approval_request.reference_type
        when "Job"
          new_status = status == :approved ? JobStatus.find_by(name: "Aprovada") : JobStatus.find_by(name: "Cancelada")
          reference.update(job_status: new_status) if new_status
        end
      end
    end
  end
end
