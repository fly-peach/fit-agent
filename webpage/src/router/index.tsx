import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../app/AppShell";
import { LoginPage } from "../pages/auth/LoginPage";
import { RegisterPage } from "../pages/auth/RegisterPage";
import { DataOverviewPage } from "../pages/data-overview/Index";
import { AssessmentList } from "../pages/assessment-center/List";
import { AssessmentCreate } from "../pages/assessment-center/Create";
import { AssessmentDetail } from "../pages/assessment-center/Detail";
import { BodyCompositionListPage } from "../pages/body-composition/List";
import { BodyCompositionCreatePage } from "../pages/body-composition/Create";
import { BodyCompositionDetailPage } from "../pages/body-composition/Detail";
import { DailyMetricsPage } from "../pages/daily-metrics/Index";
import { DailyEnergyWorkoutPage } from "../pages/daily-energy-workout/Index";
import { ProtectedRoute } from "./ProtectedRoute";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="data-overview" replace />} />
        <Route path="data-overview" element={<DataOverviewPage />} />
        <Route path="dashboard" element={<Navigate to="data-overview" replace />} />
        <Route path="growth-analytics" element={<Navigate to="data-overview" replace />} />
        <Route path="daily-metrics" element={<DailyMetricsPage />} />
        <Route path="daily-energy-workout" element={<DailyEnergyWorkoutPage />} />
        <Route path="daily-workout" element={<Navigate to="/daily-energy-workout" replace />} />
        <Route path="daily-nutrition" element={<Navigate to="/daily-energy-workout" replace />} />
        <Route path="assessment-center" element={<AssessmentList />} />
        <Route path="assessment-center/new" element={<AssessmentCreate />} />
        <Route path="assessment-center/:id" element={<AssessmentDetail />} />
        <Route path="body-composition" element={<BodyCompositionListPage />} />
        <Route path="body-composition/new" element={<BodyCompositionCreatePage />} />
        <Route path="body-composition/:id" element={<BodyCompositionDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/data-overview" replace />} />
    </Routes>
  );
}
