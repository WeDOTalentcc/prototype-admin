# app/controllers/concerns/authorizable_resource.rb
module AuthorizableResource
  extend ActiveSupport::Concern

  included do
    before_action :load_resource, only: %i[show update destroy]
    before_action :authorize_resource!, only: %i[show update destroy]
    before_action :authorize_resource_class!, only: %i[create]
  end

  private

  def load_resource
    resource_name = controller_name.singularize
    instance_variable_set("@#{resource_name}", resource_class.find(params[:id]))
  end

  def authorize_resource!
    authorize resource
  end

  def authorize_resource_class!
    authorize resource_class
  end

  def resource
    instance_variable_get("@#{controller_name.singularize}")
  end

  def resource_class
    controller_name.classify.constantize
  end
end
