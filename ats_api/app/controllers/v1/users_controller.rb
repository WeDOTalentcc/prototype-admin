# frozen_string_literal: true

module V1
  class UsersController < ApplicationController
    include Authenticable
    include SearchParams
    include SearchRenderer
    include RenderDefault

    before_action :authorize_request
    before_action :set_user, only: %i[show update destroy send_invite]

    def index
      perform_search(
        model: User,
        serializer: UserSerializer
      )
    end

    def search
      perform_search(
        model: User,
        serializer: UserSerializer
      )
    end

    def show
      render_success(@user, serializer: UserSerializer)
    end

    def create
      params_hash = user_params
      role_ids = params_hash.delete(:role_ids)
      permission_ids = params_hash.delete(:permission_ids)
      admin_flag = params_hash.delete(:is_admin)
      if params_hash[:password].blank?
        params_hash[:password] = SecureRandom.hex(10)
      end
      @user = User.new(params_hash.merge(account_id: @current_user.account_id))

      if @user.save
        update_user_roles(role_ids) if role_ids.present?
        update_user_permissions(permission_ids) if permission_ids.present?
        sync_admin_role(admin_flag) unless admin_flag.nil?
        return render_success(@user, serializer: UserSerializer, status: :created)
      end
      render_error(@user, status: :unprocessable_entity)
    end

    def send_invite
      if create_and_send_invite_token
        render json: { message: "Convite enviado com sucesso" }, status: :ok
      else
        render_error(@token || @user, status: :unprocessable_entity)
      end
    end

    def update
      params_hash = user_params
      role_ids = params_hash.delete(:role_ids)
      permission_ids = params_hash.delete(:permission_ids)
      admin_flag = params_hash.delete(:is_admin)

      if @user.update(params_hash)
        update_user_roles(role_ids) if role_ids.present?
        update_user_permissions(permission_ids) if permission_ids.present?
        sync_admin_role(admin_flag) unless admin_flag.nil?
        render_success(@user, serializer: UserSerializer)
      else
        render_error(@user)
      end
    end

    def destroy
      @user.destroy
      render_success(@user, serializer: UserSerializer)
    end

    private

    def set_user
      @user = User.find_by(id: params[:id])
      render_not_found("User") unless @user
    end

    def authorize_user_action
      policy = UserPolicy.new(@current_user, @user || User)

      action = action_name.to_sym
      unless policy.public_send("#{action}?")
        render json: { error: "Acesso negado. Você precisa ser admin." }, status: :forbidden
      end
    end

    def user_params
      policy = UserPolicy.new(@current_user, @user || User)
      params.require(:user).permit(*policy.permitted_attributes)
    end

    def update_user_roles(role_ids)
      @user.user_roles.destroy_all
      role_ids.each do |role_id|
        @user.user_roles.create(role_id: role_id)
      end
    end

    def update_user_permissions(permission_ids)
      @user.user_permissions.destroy_all
      permission_ids.each do |permission_id|
        @user.user_permissions.create(permission_id: permission_id)
      end
    end

    def sync_admin_role(flag)
      admin_role = Role.find_by(name: "admin")
      return unless admin_role

      if ActiveModel::Type::Boolean.new.cast(flag)
        @user.user_roles.find_or_create_by(role_id: admin_role.id)
      else
        @user.user_roles.where(role_id: admin_role.id).destroy_all
      end
    end

    def create_and_send_invite_token
      @token = PasswordResetToken.new(
        user: @user,
        account: @user.account,
        ip_address: request.remote_ip || "0.0.0.0",
        expires_at: 7.days.from_now
      )

      if @token.save
        PasswordResetMailer.with(
          user: @user,
          token: @token.raw_token,
          reset_url: password_reset_url(@token.raw_token)
        ).new_access_email.deliver_now
        true
      else
        false
      end
    end

    def password_reset_url(token)
      frontend_url = ENV.fetch("FRONT_URL", "http://localhost:3000")
      "#{frontend_url}/reset-password/#{token}"
    end
  end
end
