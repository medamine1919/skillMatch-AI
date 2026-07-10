import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { UsersComponent } from './pages/users/users.component';
import { AnalyticsComponent } from './pages/analytics/analytics.component';

const routes: Routes = [
  { path: 'users', component: UsersComponent },
  { path: 'analytics', component: AnalyticsComponent },
  { path: '', redirectTo: 'analytics', pathMatch: 'full' }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AdminRoutingModule {}
