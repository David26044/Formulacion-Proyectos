import { Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { AuthGuard } from './auth/auth.guard';
import { AlertsSettingsComponent } from './alerts/alerts-settings.component';
import { PublicPanelComponent } from './public-panel/public-panel.component';
import { MetodologiaComponent } from './metodologia/metodologia.component';


export const routes: Routes = [
  {
    path: 'panel-publico',
    component: PublicPanelComponent
  },
  {
    path: 'metodologia',
    component: MetodologiaComponent
  },
  {
    path: 'auth',
    loadChildren: () => import('./auth/auth.routes').then(m => m.AUTH_ROUTES),
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [AuthGuard],
  },
    {
    path: 'alerts',
    component: AlertsSettingsComponent,
    canActivate: [AuthGuard],
  },
  { path: '', redirectTo: 'panel-publico', pathMatch: 'full' },
  { path: '**', redirectTo: 'panel-publico' }
];
