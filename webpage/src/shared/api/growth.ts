import { getDashboardMe } from "./dashboard";

export async function getGrowthAnalytics() {
  const data = await getDashboardMe();
  return data.growth_analytics;
}
