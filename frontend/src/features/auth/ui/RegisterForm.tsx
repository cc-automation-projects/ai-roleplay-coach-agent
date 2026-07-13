import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from '@tanstack/react-router';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { ConsentCheckbox } from './ConsentCheckbox';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'react-hot-toast';

const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, 'Имя пользователя должно содержать минимум 3 символа')
      .max(32, 'Имя пользователя не должно превышать 32 символа')
      .regex(/^[a-zA-Z0-9_]+$/, 'Только латиница, цифры и нижнее подчёркивание'),
    password: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
    confirmPassword: z.string(),
    consent: z.boolean().refine((v) => v === true, 'Необходимо согласие на обработку ПДн'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export const RegisterForm: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { consent: false },
  });

  const onSubmit = async (data: RegisterFormValues) => {
    setIsLoading(true);
    try {
      await registerUser(data.username, data.password);
      await navigate({ to: '/' });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Ошибка регистрации. Попробуйте позже.';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const consentValue = watch('consent');

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Регистрация</CardTitle>
        <CardDescription>Создайте аккаунт для доступа к тренажёру</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Логин</Label>
            <Input
              id="username"
              placeholder="Придумайте логин"
              {...register('username')}
              disabled={isLoading}
            />
            {errors.username && (
              <p className="text-sm text-destructive">{errors.username.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Пароль</Label>
            <Input
              id="password"
              type="password"
              placeholder="Минимум 8 символов"
              {...register('password')}
              disabled={isLoading}
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Подтверждение пароля</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Повторите пароль"
              {...register('confirmPassword')}
              disabled={isLoading}
            />
            {errors.confirmPassword && (
              <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
            )}
          </div>

          <ConsentCheckbox
            checked={consentValue}
            onCheckedChange={(checked) => setValue('consent', checked as boolean)}
          />
          {errors.consent && <p className="text-sm text-destructive">{errors.consent.message}</p>}

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
          </Button>
          <div className="text-center text-sm text-muted-foreground">
            Уже есть аккаунт?{' '}
            <a href="/login" className="text-primary hover:underline">
              Войти
            </a>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
