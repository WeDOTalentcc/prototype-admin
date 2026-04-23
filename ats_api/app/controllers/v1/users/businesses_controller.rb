module V1
  module Users
    class BusinessesController < ApplicationController
      include AuthorizableResource

      before_action :set_business, only: %i[show update destroy generate_big_five]

      def index
        authorize Business
        skip_policy_scope

        search_conditions = {}

        unless @current_user.has_role?(:super_admin)
          search_conditions[:where] = {}
          search_conditions[:where][:account_id] = @current_user.account_id
        end

        perform_search(
          model: Business,
          serializer: BusinessSerializer,
          search_with_pin: search_with_pin.merge(search_conditions)
        )
      end

      def show
        render_success(@business, serializer: BusinessSerializer)
      end

      def update
        if @business.update(business_params)
          @business.logo.attach(params[:business][:logo]) if params[:business][:logo].present?
          @business.cover_image.attach(params[:business][:cover_image]) if params[:business][:cover_image].present?
          return render_success(@business, serializer: BusinessSerializer)
        end
        render_error(@business)
      end

      def destroy
        @business.update(is_active: false)
        render_success(@business, serializer: BusinessSerializer)
      end

      def create
        @business = Business.new(business_params)
        @business.account_id = @current_user.account_id if @business.account_id.blank?
        @business.logo.attach(params[:business][:logo]) if params[:business][:logo].present?
        @business.cover_image.attach(params[:business][:cover_image]) if params[:business][:cover_image].present?

        if @business.save
          return render_success(@business, serializer: BusinessSerializer)
        end
        render_error(@business)
      end

      def generate_big_five
        result = BusinessBigFiveService.call(business: @business)

        if result[:success]
          @business.reload
          render_success(@business, serializer: BusinessSerializer)
        else
          render_simple_error(result[:error] || "Falha ao gerar perfil Big Five")
        end
      end

      private

      def set_business
        @business = Business.find(params[:id])
        authorize @business
      end

      def business_params
        params.require(:business).permit(
          :name,
          :cnpj,
          :email,
          :phone,
          :website,
          :address,
          :industry,
          :size,
          :linkedin,
          :about,
          :is_active,
          :corporate_name,
          :job_amount,
          :logo,
          :cover_image,
          :mission,
          :vision,
          :work_model,
          :growth_opportunities,
          :team_dynamics,
          :leader_style,
          :evp_highlights,
          :diversity_and_inclusion,
          :sustainability,
          :social_impact,
          :openness,
          :conscientiousness,
          :extraversion,
          :agreeableness,
          :stability,
          culture_values: [],
          soft_skills: []
        )
      end
    end
  end
end
