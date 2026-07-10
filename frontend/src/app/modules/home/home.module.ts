import { NgModule } from '@angular/core';
import { IconComponent } from '../../shared/icon/icon.component';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HomeRoutingModule } from './home-routing.module';
import { LandingComponent } from './pages/landing/landing.component';

@NgModule({
  declarations: [LandingComponent],
  imports: [
    CommonModule,
    RouterModule,
    HomeRoutingModule, IconComponent
  ]
})
export class HomeModule { }
