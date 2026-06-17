
module RenderDefault
  extend ActiveSupport::Concern

  def render_success(resource, status: :ok, serializer: nil, meta: nil, serializer_params: {})
    if serializer
      options = {
        meta: meta,
        params: serializer_params
      }.compact

      if respond_to?(:sparse_fields_for, true)
        sparse_fields = sparse_fields_for(serializer)
        options[:fields] = { extract_resource_type(serializer) => sparse_fields } if sparse_fields.present?
      end

      return render json: serializer.new(resource, options).serializable_hash, status: status
    end

    render json: resource, status: status
  end

  def render_error(resource, status: :unprocessable_entity)
    if resource.is_a?(Hash) && resource.key?(:errors)
      render json: { errors: resource[:errors] }, status: status
    elsif resource.respond_to?(:errors) && resource.errors.present?
      render json: { errors: resource.errors.full_messages }, status: status
    else
      render json: { errors: [ "Erro desconhecido" ] }, status: status
    end
  end

  def render_error_message(msg)
    render json: { errors: [ msg ] }, status: :unprocessable_entity
  end

  def render_simple_error(message, status: :bad_request)
    render json: { errors: [ message ] }, status: status
  end

  def render_not_found(entity = "Recurso")
    render_simple_error("#{entity} não encontrado", status: :not_found)
  end

  def render_no_content
    head :no_content
  end

  private

  def extract_resource_type(serializer_class)
    serializer_class.name.demodulize.underscore.gsub("_serializer", "").to_sym
  end
end
