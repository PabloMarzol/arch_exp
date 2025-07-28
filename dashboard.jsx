import React, { useState, useEffect } from 'react';
import { 
  Grid, Card, CardContent, Typography, 
  Table, TableBody, TableCell, TableHead, TableRow,
  Alert, Chip, LinearProgress 
} from '@mui/material';
import { 
  TrendingUp, Inventory, Warning, Factory,
  ShoppingCart, Receipt, Sync 
} from '@mui/icons-material';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [syncStatus, setSyncStatus] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    fetchSyncStatus();
    
    // Set up real-time updates
    const interval = setInterval(() => {
      fetchSyncStatus();
    }, 30000); // Check sync status every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/analytics/dashboard');
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch('/api/sync/status');
      const status = await response.json();
      setSyncStatus(status);
    } catch (error) {
      console.error('Error fetching sync status:', error);
    }
  };

  if (loading) return <LinearProgress />;

  return (
    <Grid container spacing={3}>
      {/* Key Metrics Cards */}
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Total Orders"
          value={dashboardData?.total_orders || 0}
          icon={<ShoppingCart />}
          color="primary"
        />
      </Grid>
      
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Revenue (30d)"
          value={`£${dashboardData?.total_revenue?.toLocaleString() || 0}`}
          icon={<TrendingUp />}
          color="success"
        />
      </Grid>
      
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Low Stock Items"
          value={dashboardData?.low_stock_items || 0}
          icon={<Warning />}
          color="warning"
        />
      </Grid>
      
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Pending Production"
          value={dashboardData?.pending_production || 0}
          icon={<Factory />}
          color="info"
        />
      </Grid>

      {/* Sync Status */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Sync /> Integration Status
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <SyncStatusIndicator 
                  platform="Shopify"
                  status={syncStatus.shopify}
                />
              </Grid>
              <Grid item xs={4}>
                <SyncStatusIndicator 
                  platform="NuOrder"
                  status={syncStatus.nuorder}
                />
              </Grid>
              <Grid item xs={4}>
                <SyncStatusIndicator 
                  platform="QuickBooks"
                  status={syncStatus.quickbooks}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Orders */}
      <Grid item xs={12} md={8}>
        <RecentOrdersTable />
      </Grid>

      {/* Production Alerts */}
      <Grid item xs={12} md={4}>
        <ProductionAlertsPanel />
      </Grid>
    </Grid>
  );
};

const MetricCard = ({ title, value, icon, color }) => (
  <Card>
    <CardContent>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={8}>
          <Typography color="textSecondary" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h4">
            {value}
          </Typography>
        </Grid>
        <Grid item xs={4}>
          <div style={{ color: `var(--${color}-main)`, fontSize: '2rem' }}>
            {icon}
          </div>
        </Grid>
      </Grid>
    </CardContent>
  </Card>
);

const SyncStatusIndicator = ({ platform, status }) => {
  const getStatusColor = (status) => {
    switch(status?.status) {
      case 'connected': return 'success';
      case 'syncing': return 'info';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <div>
      <Typography variant="body2" color="textSecondary">
        {platform}
      </Typography>
      <Chip 
        label={status?.status || 'Unknown'}
        color={getStatusColor(status)}
        size="small"
      />
      {status?.last_sync && (
        <Typography variant="caption" display="block">
          Last sync: {new Date(status.last_sync).toLocaleString()}
        </Typography>
      )}
    </div>
  );
};