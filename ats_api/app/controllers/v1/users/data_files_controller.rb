# frozen_string_literal: true

module V1
  module Users
    class DataFilesController < ApplicationController
      include ResourceLoader

      before_action :set_active_storage_host, only: [ :create, :update ]

      def index
        perform_search(
          model: DataFile,
          serializer: DataFileSerializer,
          search_with_pin: search_with_pin.merge(
            where: {
              user_id: @current_user.id,
              is_deleted: false,
              account_id: @current_user.account_id
           }
          ),
        )
      end

      def show
        render_success(@data_file, serializer: DataFileSerializer)
      end

      def create
        if avoid_duplicate?
          try_update_existing_data_file and return
        end

        @data_file = @current_user.data_files.build(data_file_params.except(:avoid_duplicate))
        @data_file.account ||= @current_user.account
        attach_file(@data_file)

        if @data_file.save
          return render_success_with_url(@data_file, message: "File uploaded successfully", status: :created)
        end

        render_error(@data_file, status: :unprocessable_entity)
      end

      def update
        if @data_file.update(data_file_params.except(:avoid_duplicate))
          attach_file(@data_file)
          return render_success(@data_file, serializer: DataFileSerializer)
        end

        render_error(@data_file)
      end

      def destroy
        @data_file.file.purge if @data_file.file.attached?
        @data_file.destroy
        render_no_content
      end

      private

      def set_active_storage_host
        if Rails.env.development? || Rails.env.test?
          ActiveStorage::Current.url_options = { host: request.base_url }
        end
      end

      def data_file_params
        params.require(:data_file).permit(
          :name, :reference_id, :reference_type, :file, :file_type,
          :is_downloaded, :is_deleted, :avoid_duplicate
        )
      end

      def avoid_duplicate?
        params.dig(:data_file, :avoid_duplicate) == "true"
      end

      def try_update_existing_data_file
        existing = DataFile.find_by(
          name: data_file_params[:name],
          reference_id: data_file_params[:reference_id],
          reference_type: data_file_params[:reference_type],
          file_type: data_file_params[:file_type],
          user: @current_user
        )

        return false unless existing

        attach_file(existing)
        if existing.update(data_file_params.except(:file, :avoid_duplicate))
          render_success_with_url(existing, message: "File updated successfully", status: :ok)
        else
          render_error(existing, status: :unprocessable_entity)
        end

        true
      end

      def attach_file(data_file)
        return unless params[:data_file]&.[](:file).present?
        data_file.file.attach(params[:data_file][:file])
      end

      def render_success_with_url(data_file, message:, status:)
        url = file_url_for(data_file)
        render json: { message:, url:, data_file_id: data_file.id }, status:
      end

      def file_url_for(data_file)
        return nil unless data_file.file.attached?

        Rails.application.routes.url_helpers.rails_blob_url(
          data_file.file,
          host: ActiveStorage::Current.url_options[:host]
        )
      end
    end
  end
end
