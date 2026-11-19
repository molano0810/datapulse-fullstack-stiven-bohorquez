import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { LoginComponent } from './features/auth/login/login.component';
import { DashboardHomeComponent } from './features/dashboard/dashboard-home/dashboard-home.component';
import { PaisesListComponent } from './features/paises/paises-list/paises-list.component';
import { RiesgoMotorComponent } from './features/riesgo/riesgo-motor/riesgo-motor.component';

export const routes: Routes = [
    { path: 'login', component: LoginComponent },
    { path: 'dashboard', component: DashboardHomeComponent, canActivate: [authGuard] },
    { path: 'paises', component: PaisesListComponent, canActivate: [authGuard] },
    { path: 'riesgo', component: RiesgoMotorComponent, canActivate: [authGuard] },
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    { path: '**', redirectTo: 'dashboard' }
];