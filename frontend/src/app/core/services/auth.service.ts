import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthResponse, Usuario } from '../models/api.models';

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private http = inject(HttpClient);
    private router = inject(Router);
    private apiUrl = `${environment.apiUrl}/auth`;

    // Estado reactivo del usuario actual usando Angular Signals
    private currentUserSignal = signal<Usuario | null>(this.getUserFromStorage());
    public currentUser = this.currentUserSignal.asReadonly();
    public isAuthenticated = computed(() => !!this.currentUserSignal());
    public isAdmin = computed(() => this.currentUserSignal()?.rol === 'ADMIN');
    public canEditPortfolios = computed(() => ['ADMIN', 'ANALISTA'].includes(this.currentUserSignal()?.rol || ''));

    login(credentials: { email: string; password: string }): Observable<AuthResponse> {
        return this.http.post<AuthResponse>(`${this.apiUrl}/login/`, credentials).pipe(
            tap((res) => {
                sessionStorage.setItem('access_token', res.access);
                sessionStorage.setItem('refresh_token', res.refresh);
                sessionStorage.setItem('user_data', JSON.stringify(res.user));
                this.currentUserSignal.set(res.user);
            })
        );
    }

    register(data: { email: string; nombre_completo: string; password: string; rol?: string }): Observable<Usuario> {
        return this.http.post<Usuario>(`${this.apiUrl}/register/`, data);
    }

    logout(): void {
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user_data');
        this.currentUserSignal.set(null);
        this.router.navigate(['/login']);
    }

    getToken(): string | null {
        return sessionStorage.getItem('access_token');
    }

    private getUserFromStorage(): Usuario | null {
        const token = sessionStorage.getItem('access_token');
        const userJson = sessionStorage.getItem('user_data');
        if (!token || !userJson || userJson === 'undefined') return null;
        try {
            return JSON.parse(userJson);
        } catch {
            return null;
        }
    }
}