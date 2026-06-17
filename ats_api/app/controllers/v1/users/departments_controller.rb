module V1
  module Users
    class DepartmentsController < ApplicationController
      before_action :set_department, only: %i[show update destroy ancestors descendants organization_chart]

      def index
        enforce_limit!
        params[:where] = (params[:where] || {}).merge(account_id: @current_user.account_id)
        params[:where][:is_deleted] ||= false

        perform_search(model: Department, serializer: DepartmentSerializer, include_aggregators: true)
      end

      def show
        render_success(@department, serializer: DepartmentSerializer)
      end

      def create
        department = build_department
        return render_error(department) unless department.save

        process_managers(department)
        render_success(department, serializer: DepartmentSerializer, status: :created)
      end

      def update
        @department.assign_attributes(department_params.except(:managers))
        @department.level = computed_level(@department.parent_department_id)
        return render_error(@department) unless @department.save

        sync_managers
        render_success(@department, serializer: DepartmentSerializer)
      end

      def destroy
        @department.update(is_deleted: true)
        render_success(@department, serializer: DepartmentSerializer)
      end

      def reorder
        return render json: { error: "items required" }, status: :unprocessable_entity if params[:items].blank?

        Department.transaction do
          params[:items].each_with_index do |item, idx|
            account_departments.where(id: item[:id]).update_all(order: idx)
          end
        end
        render json: { message: "Ordem atualizada" }, status: :ok
      end

      def import
        data_file = resolve_data_file
        return unless data_file
        return process_async_import(data_file) if async_import?

        render json: ::BulkImports::DepartmentsImporterService.call(data_file_id: data_file.id, user_id: @current_user.id), status: :ok
      end

      def tree
        render json: root_departments.map { |d| build_tree(d) }
      end

      def organization_chart
        render json: build_org_chart(@department)
      end

      def ancestors
        render json: { ancestors: @department.ancestors.map { |d| simple_hash(d) } }
      end

      def descendants
        render json: { descendants: @department.descendants.map { |d| simple_hash(d) } }
      end

      private

      def account_departments
        Department.where(account_id: @current_user.account_id)
      end

      def root_departments
        account_departments.where(parent_department_id: nil, is_deleted: false).order(:order, :name)
      end

      def build_department
        dept = Department.new(department_params.except(:managers))
        dept.account_id = @current_user.account_id
        dept.level = computed_level(dept.parent_department_id)
        dept
      end

      def resolve_data_file
        return create_data_file_from_upload if params[:file].present?
        return find_existing_data_file if params[:data_file_id].present?

        render json: { error: "Envie 'file' ou 'data_file_id'" }, status: :unprocessable_entity
        nil
      end

      def create_data_file_from_upload
        data_file = DataFile.new(user: @current_user, account: @current_user.account, name: params[:file].original_filename)
        data_file.file.attach(params[:file])
        return data_file if data_file.save

        render json: { error: data_file.errors.full_messages }, status: :unprocessable_entity
        nil
      end

      def find_existing_data_file
        data_file = DataFile.find_by(id: params[:data_file_id], account_id: @current_user.account_id)
        return data_file if data_file

        render json: { error: "Arquivo não encontrado" }, status: :not_found
        nil
      end

      def async_import?
        params[:async].to_s == "true"
      end

      def process_async_import(data_file)
        DepartmentImportJob.perform_later(data_file_id: data_file.id, user_id: @current_user.id)
        render json: { message: "Importação iniciada em background" }, status: :accepted
      end

      def department_params
        params.require(:department).permit(
          :name, :description, :parent_department_id, :manager_id, :manager_name,
          :manager_email, :manager_title, :color, :headcount, :order,
          managers: %i[id name email title is_primary]
        )
      end

      def set_department
        @department = account_departments.find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Departamento")
      end

      def computed_level(parent_id)
        return 0 unless parent_id

        account_departments.find_by(id: parent_id)&.level.to_i + 1
      end

      def build_tree(dept)
        { id: dept.id, name: dept.name, manager: dept.manager&.name, level: dept.level,
          children: dept.child_departments.map { |c| build_tree(c) } }
      end

      def build_org_chart(dept)
        {
          department: dept.name,
          manager: dept.manager&.name,
          positions: dept.organizational_positions.includes(:direct_reports, :reports_to).map { |p| position_hash(p) },
          teams: dept.teams.includes(:team_lead).map { |t| team_hash(t) }
        }
      end

      def position_hash(pos)
        { id: pos.id, title: pos.title, current_holder: pos.current_user&.name,
          reports_to: pos.reports_to&.title, direct_reports_count: pos.direct_reports.count }
      end

      def team_hash(team)
        { id: team.id, name: team.name, lead: team.team_lead&.name,
          member_count: team.member_count, members: team.current_composition }
      end

      def simple_hash(dept)
        { id: dept.id, name: dept.name, manager: dept.manager&.name, level: dept.level }
      end

      def managers_data
        params.dig(:department, :managers) || []
      end

      def process_managers(department)
        return if managers_data.blank?

        primary_set = false
        managers_data.each do |data|
          next if data[:id].blank? && data[:name].blank?

          is_primary = data[:is_primary].presence || !primary_set
          primary_set = true if is_primary
          create_manager_relationship(department, data, is_primary)
        end
      end

      def sync_managers
        return if managers_data.blank?

        remove_old_managers
        primary_set = false

        managers_data.each do |data|
          next if data[:id].blank? && data[:name].blank?

          is_primary = data[:is_primary].presence || !primary_set
          primary_set = true if is_primary
          upsert_manager(data, is_primary)
        end
      end

      def remove_old_managers
        existing_ids = @department.department_relationships.managers.pluck(:user_id).compact
        new_ids = managers_data.filter_map { |m| m[:id] }
        ids_to_remove = existing_ids - new_ids
        @department.department_relationships.managers.where(user_id: ids_to_remove).update_all(is_deleted: true) if ids_to_remove.any?
      end

      def upsert_manager(data, is_primary)
        existing = data[:id].present? && @department.department_relationships.managers.find_by(user_id: data[:id])
        return update_existing_manager(existing, data, is_primary) if existing

        create_manager_relationship(@department, data, is_primary)
      end

      def update_existing_manager(rel, data, is_primary)
        rel.update(title: data[:title], is_primary: is_primary, is_deleted: false)
        update_department_manager(data) if is_primary
      end

      def create_manager_relationship(department, data, is_primary)
        rel = department.department_relationships.new(
          account_id: @current_user.account_id,
          role: "manager",
          is_primary: is_primary,
          title: data[:title]
        )

        assign_reference(rel, department, data)
        update_department_manager(data, department) if is_primary
        rel.save
      end

      def assign_reference(rel, department, data)
        if data[:id].present?
          rel.assign_attributes(user_id: data[:id], reference_type: "User", reference_id: data[:id])
        else
          rel.assign_attributes(reference_type: "Department", reference_id: department.id)
        end
      end

      def update_department_manager(data, department = @department)
        department.update(
          manager_id: data[:id],
          manager_name: data[:name],
          manager_email: data[:email],
          manager_title: data[:title]
        )
      end

      def enforce_limit!(max = 100)
        val = (params[:limit].presence || params[:per_page].presence).to_i
        params[:limit] = val.between?(1, max) ? val : max
      end
    end
  end
end
