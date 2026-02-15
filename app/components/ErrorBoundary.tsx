'use client';

import React, { ReactNode, ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error: error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error);
    console.error('Error info:', errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f5f7fa',
          padding: '20px'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '40px',
            maxWidth: '500px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            textAlign: 'center'
          }}>
            <h1 style={{
              fontSize: '2rem',
              color: '#ef4444',
              marginBottom: '16px'
            }}>
              ⚠️ Что-то пошло не так
            </h1>
            
            <p style={{
              color: '#666',
              marginBottom: '24px',
              lineHeight: '1.6'
            }}>
              {this.state.error?.message || 'Произошла неожиданная ошибка. Пожалуйста, согласитесь с действиями.'}
            </p>

            {process.env.NODE_ENV === 'development' && (
              <details style={{
                textAlign: 'left',
                marginBottom: '24px',
                padding: '12px',
                backgroundColor: '#f8fafc',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#666'
              }}>
                <summary style={{ cursor: 'pointer', fontWeight: '600' }}>
                  Детали ошибки (режим разработки)
                </summary>
                <pre style={{
                  marginTop: '12px',
                  overflow: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word'
                }}>
                  {this.state.error?.toString()}
                </pre>
              </details>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={this.handleReset}
                style={{
                  flex: 1,
                  padding: '12px 24px',
                  backgroundColor: '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = '#2980b9'}
                onMouseOut={(e) => e.currentTarget.style.background = '#3498db'}
              >
                Попробовать снова
              </button>
              
              <a
                href="/"
                style={{
                  flex: 1,
                  padding: '12px 24px',
                  backgroundColor: '#ecf0f1',
                  color: '#333',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = '#d5dbdb'}
                onMouseOut={(e) => e.currentTarget.style.background = '#ecf0f1'}
              >
                На главную
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
