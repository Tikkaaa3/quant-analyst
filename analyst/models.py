from django.db import models


class AnalysisReport(models.Model):
    ticker = models.CharField(max_length=10)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    prediction_score = models.FloatField()
    sentiment = models.JSONField()
    ai_report = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticker} - {self.created_at.strftime('%Y-%m-%d')}"
