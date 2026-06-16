# frozen_string_literal: true

module V1
  module Users
    class SectorsController < ApplicationController
      before_action :set_sector, only: [ :show, :update, :destroy ]

      def index
        authorize Sector

        params[:where] ||= {}
        params[:where][:is_deleted] = false unless params[:where].key?(:is_deleted)

        if params[:where][:is_public].nil?
          params[:where][:_or] = [
            { is_public: true, account_id: nil },
            { account_id: @current_user.account_id }
          ]
        end

        # Habilita autocomplete quando houver termo de busca
        params[:match] = :word_start if params[:term].present?

        params[:extra_params] = {
          include_children: params[:include_children].present?,
          include_ancestors: params[:include_ancestors].present?,
          include_siblings: params[:include_siblings].present?
        }

        perform_search(
          model: Sector,
          serializer: SectorSerializer
        )
      end

      def show
        authorize @sector

        render_success(@sector,
          serializer: SectorSerializer,
          serializer_params: {
            extra_params: {
              include_children: params[:include_children].present?,
              include_ancestors: params[:include_ancestors].present?,
              include_siblings: params[:include_siblings].present?
            }
          }
        )
      end

      def create
        authorize Sector

        @sector = Sector.new(sector_params)

        # Se não for super_admin, força account_id e is_public
        unless @current_user.has_role?(:super_admin)
          @sector.account_id = @current_user.account_id
          @sector.is_public = false
        end

        if @sector.save
          return render_success(@sector, serializer: SectorSerializer, status: :created)
        end

        render_error(@sector, status: :unprocessable_entity)
      end

      def update
        authorize @sector

        if @sector.update(sector_params)
          return render_success(@sector, serializer: SectorSerializer)
        end

        render_error(@sector, status: :unprocessable_entity)
      end

      def destroy
        authorize @sector

        if @sector.destroy
          return render_success(@sector, serializer: SectorSerializer)
        end

        render_error(@sector, status: :unprocessable_entity)
      end

      def tree
        authorize Sector, :tree?

        params[:where] ||= {}
        params[:where][:is_deleted] = false
        params[:where][:parent_sector_id] = nil # Apenas raízes

        # Adiciona filtro para setores públicos ou da conta do usuário
        params[:where][:_or] = [
          { is_public: true, account_id: nil },
          { account_id: @current_user.account_id }
        ]

        params[:extra_params] = { include_children: true }

        perform_search(
          model: Sector,
          serializer: SectorSerializer
        )
      end

      def autocomplete
        authorize Sector

        params[:where] ||= {}
        params[:where][:is_deleted] = false
        params[:where][:_or] = [
          { is_public: true, account_id: nil },
          { account_id: @current_user.account_id }
        ]

        params[:match] = :word_start
        params[:per_page] = 10

        perform_search(
          model: Sector,
          serializer: SectorSerializer
        )
      end

      private

      def set_sector
        @sector = Sector.active.find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render json: { error: "Setor não encontrado" }, status: :not_found
      end

      def sector_params
        params.require(:sector).permit(
          :name,
          :description,
          :parent_sector_id,
          :icon,
          :is_public,
          :account_id,
          tags: []
        )
      end
    end
  end
end
