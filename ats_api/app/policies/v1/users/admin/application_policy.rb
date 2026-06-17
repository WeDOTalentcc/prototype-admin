module V1
  module Users
    module Admin
      class ApplicationPolicy < ::ApplicationPolicy
        def access_admin_area?
          user.present? && (user.has_role?(:admin) || user.has_role?(:super_admin))
        end
      end
    end
  end
end
