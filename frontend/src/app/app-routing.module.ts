import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from './guards/auth.guard';

const routes: Routes = [
  { path: '', redirectTo: '/auth/login', pathMatch: 'full' },
  {
    path: 'auth',
    loadChildren: () => import('./modules/auth/auth.module').then(m => m.AuthModule)
  },
  {
    path: 'home',
    loadChildren: () => import('./modules/home/home.module').then(m => m.HomeModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'dashboard',
    loadChildren: () => import('./modules/dashboard/dashboard.module').then(m => m.DashboardModule),
    canActivate: [AuthGuard],
    data: { roles: ['ADMIN_RH', 'RECRUITER', 'USER'] }
  },
  {
    path: 'candidates',
    loadChildren: () => import('./modules/candidates/candidates.module').then(m => m.CandidatesModule),
    canActivate: [AuthGuard],
    data: { roles: ['ADMIN_RH', 'RECRUITER', 'USER'] }
  },
  {
    path: 'upload',
    loadChildren: () => import('./modules/upload/upload.module').then(m => m.UploadModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'admin',
    loadChildren: () => import('./modules/admin/admin.module').then(m => m.AdminModule),
    canActivate: [AuthGuard],
    data: { roles: ['ADMIN_RH'] }
  },
  {
    // Tableau de bord des tests (recruteur connecté)
    path: 'tests',
    loadComponent: () => import('./modules/tests/pages/tests-dashboard/tests-dashboard.component').then(m => m.TestsDashboardComponent),
    canActivate: [AuthGuard],
    data: { roles: ['ADMIN_RH', 'RECRUITER', 'USER'] }
  },
  {
    // Dashboard analytique des tests (KPI + graphiques), recruteur connecté
    path: 'tests-dashboard',
    loadComponent: () => import('./modules/tests/pages/test-analytics/test-analytics.component').then(m => m.TestAnalyticsComponent),
    canActivate: [AuthGuard],
    data: { roles: ['ADMIN_RH', 'RECRUITER', 'USER'] }
  },
  {
    // Passage du test par le candidat (PUBLIC, sans login, via jeton)
    path: 'test',
    loadComponent: () => import('./modules/tests/pages/public-test/public-test.component').then(m => m.PublicTestComponent)
  },
  { path: 'unauthorized', loadChildren: () => import('./modules/error/error.module').then(m => m.ErrorModule) },
  { path: 'invalid-document', loadComponent: () => import('./modules/error/pages/invalid-document/invalid-document.component').then(m => m.InvalidDocumentComponent) },
  { path: '**', redirectTo: '/auth/login' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
