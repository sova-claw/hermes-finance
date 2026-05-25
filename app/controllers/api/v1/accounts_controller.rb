# frozen_string_literal: true

class Api::V1::AccountsController < Api::V1::BaseController
  include Pagy::Backend

  before_action :ensure_read_scope, only: %i[index show]
  before_action :ensure_write_scope, only: %i[create]

  def index
    @per_page = safe_per_page_param

    @pagy, @accounts = pagy(
      accounts_scope.alphabetically,
      page: safe_page_param,
      limit: @per_page
    )

    render :index
  rescue => e
    Rails.logger.error "AccountsController#index error: #{e.message}"
    Rails.logger.error e.backtrace.join("\n")

    render json: {
      error: "internal_server_error",
      message: "An unexpected error occurred"
    }, status: :internal_server_error
  end

  def show
    unless valid_uuid?(params[:id])
      render json: {
        error: "not_found",
        message: "Account not found"
      }, status: :not_found
      return
    end

    @account = accounts_scope.find(params[:id])

    render :show
  rescue ActiveRecord::RecordNotFound
    render json: {
      error: "not_found",
      message: "Account not found"
    }, status: :not_found
  rescue => e
    Rails.logger.error "AccountsController#show error: #{e.message}"
    Rails.logger.error e.backtrace.join("\n")

    render json: {
      error: "internal_server_error",
      message: "An unexpected error occurred"
    }, status: :internal_server_error
  end

  def create
    accountable_type = account_params[:accountable_type].presence || "Depository"
    unless %w[Depository CreditCard Loan Investment].include?(accountable_type)
      render json: { error: "invalid_accountable_type", message: "accountable_type must be one of: Depository, CreditCard, Loan, Investment" }, status: :unprocessable_entity
      return
    end

    @account = Account.create_and_sync({
      family: current_resource_owner.family,
      name: account_params[:name],
      balance: account_params[:balance].presence || 0,
      currency: account_params[:currency].presence || current_resource_owner.family.currency,
      accountable_type: accountable_type,
      accountable_attributes: {}
    })

    if @account.persisted?
      render :show, status: :created
    else
      render json: { error: "validation_failed", message: @account.errors.full_messages.join(", ") }, status: :unprocessable_entity
    end
  rescue => e
    Rails.logger.error "AccountsController#create error: #{e.message}"
    render json: { error: "internal_server_error", message: "An unexpected error occurred" }, status: :internal_server_error
  end

  private

    def ensure_read_scope
      authorize_scope!(:read)
    end

    def ensure_write_scope
      authorize_scope!(:write)
    end

    def account_params
      params.require(:account).permit(:name, :currency, :balance, :accountable_type)
    end

    def accounts_scope
      scope = current_resource_owner.family.accounts
                                    .accessible_by(current_resource_owner)
                                    .includes(:accountable, account_providers: :provider)
      include_disabled_accounts? ? scope : scope.visible
    end

    def include_disabled_accounts?
      ActiveModel::Type::Boolean.new.cast(params[:include_disabled])
    end
end
