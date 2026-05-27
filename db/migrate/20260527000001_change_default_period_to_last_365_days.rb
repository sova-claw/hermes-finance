class ChangeDefaultPeriodToLast365Days < ActiveRecord::Migration[7.2]
  def up
    change_column_default :users, :default_period, from: "last_30_days", to: "last_365_days"
    User.where(default_period: "last_30_days").update_all(default_period: "last_365_days")
  end

  def down
    change_column_default :users, :default_period, from: "last_365_days", to: "last_30_days"
    User.where(default_period: "last_365_days").update_all(default_period: "last_30_days")
  end
end
