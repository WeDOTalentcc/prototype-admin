
module V1
  module Users
    module Admin
      class ApplicationController < V1::Users::ApplicationController
        include Pundit::Authorization
        include AuthorizableResource

        before_action :authorize_admin_access
        after_action :verify_authorized, except: :index
        after_action :verify_policy_scoped, only: :index

        private

        def authorize_admin_access
          authorize self, :access_admin_area?, policy_class: V1::Users::Admin::ApplicationPolicy
        end

        def pundit_user
          @current_user
        end
      end
    end
  end
end
