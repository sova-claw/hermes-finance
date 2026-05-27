class MonobankSync
  RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2".freeze

  SyncHealth = Data.define(:last_imported_at, :count_last_24h) do
    def status
      return :unknown if last_imported_at.nil?
      hours_ago = (Time.current - last_imported_at) / 1.hour
      if hours_ago < 48 then :fresh
      elsif hours_ago < 168 then :aging
      else :stale
      end
    end
  end

  def self.health(family)
    scope = Entry.joins(:account).where(source: "monobank", accounts: { family_id: family.id })
    SyncHealth.new(
      last_imported_at: scope.maximum(:created_at),
      count_last_24h: scope.where(created_at: 24.hours.ago..).count
    )
  end

  def self.stats(family)
    Entry
      .joins(:account)
      .where(source: "monobank", accounts: { family_id: family.id })
      .group("accounts.id", "accounts.name", "accounts.currency")
      .select("accounts.id, accounts.name, accounts.currency, COUNT(*) AS entry_count, MAX(entries.date) AS last_entry_date, MIN(entries.date) AS first_entry_date")
      .order("MAX(entries.date) DESC")
  end

  def self.trigger!(service_id:, api_token:)
    require "net/http"

    uri = URI(RAILWAY_API_URL)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true

    request = Net::HTTP::Post.new(uri)
    request["Authorization"] = "Bearer #{api_token}"
    request["Content-Type"] = "application/json"
    request.body = JSON.generate({
      query: %(mutation { serviceInstanceRedeploy(serviceId: "#{service_id}") })
    })

    http.request(request).is_a?(Net::HTTPSuccess)
  end
end
