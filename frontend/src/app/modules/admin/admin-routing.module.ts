import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { UsersComponent } from './pages/users/users.component';
import { AnalyticsComponent } from './pages/analytics/analytics.component';
import { ModelEvaluationComponent } from './pages/model-evaluation/model-evaluation.component';

const routes: Routes = [
  { path: 'users', component: UsersComponent },
  { path: 'analytics', component: AnalyticsComponent },
  { path: 'evaluation', component: ModelEvaluationComponent },
  { path: '', redirectTo: 'analytics', pathMatch: 'full' }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AdminRoutingModule {}
