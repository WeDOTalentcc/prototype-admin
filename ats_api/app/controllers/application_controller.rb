class ApplicationController < ActionController::Base
  include Authenticable
  include SparseFieldsets

  skip_before_action :verify_authenticity_token

  before_action :set_current_ip

  private

  def set_current_ip
    Current.ip = request.remote_ip
  end
end
