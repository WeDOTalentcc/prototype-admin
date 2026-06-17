module ResourceLoader
  extend ActiveSupport::Concern
  include RenderDefault

  included do
    before_action :set_resource, only: %i[show update destroy]
  end

  private

  def set_resource
    klass = controller_name.classify.constantize
    query = klass.all

    query = query.include_base if klass.respond_to?(:include_base)

    if klass.column_names.include?("account_id") && @current_user
      query = query.where(account_id: @current_user.account_id)
    end

    resource = query.find_by(id: params[:id])

    instance_variable_set("@#{controller_name.singularize}", resource)

    render_not_found(klass.model_name.human) unless resource
  end
end
