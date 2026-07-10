import { NgModule } from '@angular/core';
import { IconComponent } from '../../shared/icon/icon.component';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { DashboardComponent } from './pages/dashboard/dashboard.component';

@NgModule({
  declarations: [
    DashboardComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    DashboardRoutingModule, IconComponent
  ]
})
export class DashboardModule { }
