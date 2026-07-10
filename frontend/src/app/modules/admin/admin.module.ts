import { NgModule } from '@angular/core';
import { IconComponent } from '../../shared/icon/icon.component';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminRoutingModule } from './admin-routing.module';
import { UsersComponent } from './pages/users/users.component';
import { AnalyticsComponent } from './pages/analytics/analytics.component';

@NgModule({
  declarations: [UsersComponent, AnalyticsComponent],
  imports: [CommonModule, FormsModule, AdminRoutingModule, IconComponent
  ]
})
export class AdminModule {}
