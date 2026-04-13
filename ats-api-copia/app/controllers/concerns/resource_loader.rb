module ResourceLoader
  extend ActiveSupport::Concern

  included do
    before_action :set_resource, only: %i[show update destroy]
  end

  private

  def set_resource
    klass = controller_name.classify.constantize
    resource = klass.find_by(id: params[:id])
    instance_variable_set("@#{controller_name.singularize}", resource)
    render_not_found(klass.name) unless resource
  end
end
