import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/auth';
import { notificationApi } from '@/services/api';

type NotificationItem = {
  id: string;
  title: string;
  body: string;
  notification_type: string;
  priority: string;
  is_read: boolean;
  data?: Record<string, any>;
  created_at: string;
};

const TYPE_ICONS: Record<string, string> = {
  info: 'i',
  warning: '!',
  urgent: '!!',
  success: 'OK',
};

const TYPE_COLORS: Record<string, string> = {
  info: '#2196F3',
  warning: '#FF9800',
  urgent: '#F44336',
  success: '#4CAF50',
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export default function NotificationsScreen() {
  const { user } = useAuthStore();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const userId = user?.id;

  const fetchNotifications = useCallback(async (pageNum: number = 1, append: boolean = false) => {
    if (!userId) {
      setLoading(false);
      return;
    }
    try {
      const data = await notificationApi.list(userId, { page: pageNum, pageSize: 20 });
      const fetched = data.items || [];
      setItems(append ? (prev) => [...prev, ...fetched] : fetched);
      setTotal(data.total || 0);
      setPage(pageNum);
    } catch {
      if (!append) setItems([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchNotifications(1);
  }, [fetchNotifications]);

  const loadMore = useCallback(() => {
    if (items.length < total) {
      fetchNotifications(page + 1, true);
    }
  }, [items.length, total, page, fetchNotifications]);

  const handleMarkAllRead = async () => {
    if (!userId) return;
    try {
      await notificationApi.markAllRead(userId);
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  };

  const handlePress = async (item: NotificationItem) => {
    if (!userId) return;

    if (!item.is_read) {
      try {
        await notificationApi.markAsRead(item.id, userId);
        setItems((prev) =>
          prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n))
        );
      } catch {}
    }

    // Navigate based on data field
    if (item.data?.route) {
      router.push(item.data.route as any);
    }
  };

  const renderItem = ({ item }: { item: NotificationItem }) => {
    const color = TYPE_COLORS[item.notification_type] || TYPE_COLORS.info;
    const icon = TYPE_ICONS[item.notification_type] || 'i';

    return (
      <TouchableOpacity
        style={[styles.card, !item.is_read && styles.cardUnread]}
        onPress={() => handlePress(item)}
        activeOpacity={0.7}
      >
        <View style={[styles.iconBadge, { backgroundColor: color }]}>
          <Text style={styles.iconText}>{icon}</Text>
        </View>
        <View style={styles.cardContent}>
          <Text style={[styles.cardTitle, !item.is_read && styles.cardTitleUnread]}>
            {item.title}
          </Text>
          <Text style={styles.cardBody} numberOfLines={2}>
            {item.body}
          </Text>
          <Text style={styles.cardTime}>{timeAgo(item.created_at)}</Text>
        </View>
        {!item.is_read && <View style={styles.unreadDot} />}
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#1B5E20" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {items.length > 0 && (
        <TouchableOpacity style={styles.markAllButton} onPress={handleMarkAllRead}>
          <Text style={styles.markAllText}>Mark All Read</Text>
        </TouchableOpacity>
      )}
      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#1B5E20" />
        }
        onEndReached={loadMore}
        onEndReachedThreshold={0.3}
        contentContainerStyle={items.length === 0 ? styles.emptyContainer : undefined}
        ListEmptyComponent={
          <View style={styles.emptyContent}>
            <Text style={styles.emptyIcon}>bell</Text>
            <Text style={styles.emptyTitle}>No Notifications</Text>
            <Text style={styles.emptySubtitle}>You're all caught up!</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  markAllButton: {
    alignSelf: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  markAllText: {
    color: '#1B5E20',
    fontSize: 14,
    fontWeight: '600',
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 12,
    marginVertical: 4,
    borderRadius: 10,
    padding: 14,
  },
  cardUnread: {
    backgroundColor: '#F1F8E9',
    borderLeftWidth: 3,
    borderLeftColor: '#1B5E20',
  },
  iconBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  iconText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: '#333',
  },
  cardTitleUnread: {
    fontWeight: '700',
    color: '#1B5E20',
  },
  cardBody: {
    fontSize: 13,
    color: '#666',
    marginTop: 2,
  },
  cardTime: {
    fontSize: 11,
    color: '#999',
    marginTop: 4,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#1B5E20',
    marginLeft: 8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  emptyContent: {
    alignItems: 'center',
    padding: 40,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
    color: '#ccc',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#999',
    marginTop: 4,
  },
});
