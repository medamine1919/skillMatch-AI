import { NgModule } from '@angular/core';
import { IconComponent } from '../../shared/icon/icon.component';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { UploadRoutingModule } from './upload-routing.module';
import { UploadComponent } from './pages/upload/upload.component';

@NgModule({
  declarations: [
    UploadComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    UploadRoutingModule, IconComponent
  ]
})
export class UploadModule { }
