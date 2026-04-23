module V1
  module Users
    module Admin
      class WhatsappConfigurationsController < ApplicationController
        before_action :set_configuration, only: [ :show, :edit, :update, :destroy, :restore ]

        def index
          authorize WhatsappConfiguration
          policy_scope(WhatsappConfiguration)

          perform_search(
            model: WhatsappConfiguration,
            serializer: WhatsappConfigurationSerializer
          )
        end

        def show
          authorize @configuration
          render_success(@configuration, serializer: WhatsappConfigurationSerializer)
        end

        def new
          @configuration = WhatsappConfiguration.new
          authorize @configuration
          render_success(@configuration, serializer: WhatsappConfigurationSerializer)
        end

        def edit
          authorize @configuration
          render_success(@configuration, serializer: WhatsappConfigurationSerializer)
        end

        def create
          @configuration = WhatsappConfiguration.new(configuration_params)
          authorize @configuration

          if @configuration.save
            return render_success(@configuration, serializer: WhatsappConfigurationSerializer, status: :created)
          end
          render_error(@configuration, status: :unprocessable_entity)
        end

        def update
          authorize @configuration

          if @configuration.update(configuration_params)
            return render_success(@configuration, serializer: WhatsappConfigurationSerializer)
          end
          render_error(@configuration, status: :unprocessable_entity)
        end

        def destroy
          authorize @configuration
          @configuration.soft_delete!
          render_success(@configuration, serializer: WhatsappConfigurationSerializer)
        end

        def restore
          authorize @configuration, :restore?
          @configuration.restore!
          render_success(@configuration, serializer: WhatsappConfigurationSerializer)
        end

        def quick_update_url
          authorize WhatsappConfiguration, :quick_update_url?
          url = params[:redirect_url]
          phone_number = params[:phone_number]
          environment = params[:environment] || Rails.env
          developer = params[:developer_name] || @current_user&.name || "Admin"

          return render json: { error: "redirect_url is required" }, status: :bad_request if url.blank?
          return render json: { error: "phone_number is required" }, status: :bad_request if phone_number.blank?

          begin
            config = WhatsappService::MessageRouter.update_local_url(
              url,
              developer_name: developer,
              phone_number: phone_number,
              environment: environment
            )
            render_success(
              config,
              serializer: WhatsappConfigurationSerializer,
              message: "URL updated successfully for #{config.formatted_phone}"
            )
          rescue => e
            render json: { error: e.message }, status: :unprocessable_entity
          end
        end

        private

        def set_configuration
          @configuration = WhatsappConfiguration.find(params[:id])
        end

        def configuration_params
          params.require(:whatsapp_configuration).permit(
            :environment, :phone_number, :redirect_url, :action_type,
            :description, :developer_name, :active, :priority,
            metadata: {}
          )
        end
      end
    end
  end
end
