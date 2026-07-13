import { NgModule } from '@angular/core';
import { IconComponent } from '../../shared/icon/icon.component';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminRoutingModule } from './admin-routing.module';
import { UsersComponent } from './pages/users/users.component';
import { AnalyticsComponent } from './pages/analytics/analytics.component';
import { ModelEvaluationComponent } from './pages/model-evaluation/model-evaluation.component';

@NgModule({
  declarations: [UsersComponent, AnalyticsComponent, ModelEvaluationComponent],
  imports: [CommonModule, FormsModule, AdminRoutingModule, IconComponent
  ]
})
export class AdminModule {}
