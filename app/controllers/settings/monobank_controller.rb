class Settings::MonobankController < ApplicationController
  layout "settings"

  def show
    @sync_stats = MonobankSync.stats(Current.family)
    @trigger_available = ENV["RAILWAY_API_TOKEN"].present? && ENV["RAILWAY_MONOBANK_SERVICE_ID"].present?
  end

  def create
    token = ENV["RAILWAY_API_TOKEN"]
    service_id = ENV["RAILWAY_MONOBANK_SERVICE_ID"]

    if token.blank? || service_id.blank?
      redirect_to settings_monobank_path, alert: t(".trigger_not_configured")
      return
    end

    if MonobankSync.trigger!(service_id: service_id, api_token: token)
      redirect_to settings_monobank_path, notice: t(".trigger_success")
    else
      redirect_to settings_monobank_path, alert: t(".trigger_failed")
    end
  end
end
