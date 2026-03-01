"""
AWS Infrastructure Setup using AWS CDK (Python)
Deploys the SDLC automation system to AWS

Components:
- Lambda functions for webhooks
- DynamoDB for storing results
- S3 for artifacts
- SNS for notifications
- EventBridge for scheduling
- CloudWatch for monitoring
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    RemovalPolicy,
    Tags
)
from constructs import Construct


class SDLCAutomationStack(Stack):
    """AWS CDK Stack for SDLC Automation"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for artifacts and reports
        artifacts_bucket = s3.Bucket(
            self, "ArtifactsBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(30)
                        )
                    ]
                )
            ]
        )

        # DynamoDB table for results
        results_table = dynamodb.Table(
            self, "ResultsTable",
            partition_key=dynamodb.Attribute(
                name="execution_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )

        # SNS Topic for alerts
        alerts_topic = sns.Topic(
            self, "AlertsTopic",
            display_name="SDLC Automation Alerts"
        )

        # Lambda execution role
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Grant permissions
        artifacts_bucket.grant_read_write(lambda_role)
        results_table.grant_read_write_data(lambda_role)
        alerts_topic.grant_publish(lambda_role)

        # Webhook Lambda function (receives GitHub webhooks)
        webhook_lambda = lambda_.Function(
            self, "WebhookLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="webhook_handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "RESULTS_TABLE": results_table.table_name,
                "ARTIFACTS_BUCKET": artifacts_bucket.bucket_name,
                "ALERTS_TOPIC_ARN": alerts_topic.topic_arn
            }
        )

        # Analysis Lambda function (runs the orchestrator)
        analysis_lambda = lambda_.Function(
            self, "AnalysisLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="analysis_handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions"),
            role=lambda_role,
            timeout=Duration.seconds(600),
            memory_size=2048,
            environment={
                "RESULTS_TABLE": results_table.table_name,
                "ARTIFACTS_BUCKET": artifacts_bucket.bucket_name,
                "ALERTS_TOPIC_ARN": alerts_topic.topic_arn
            }
        )

        # EventBridge rule to trigger analysis on schedule
        scheduled_rule = events.Rule(
            self, "ScheduledAnalysisRule",
            schedule=events.Schedule.cron(hour="0", minute="0")  # Daily at midnight
        )
        scheduled_rule.add_target(targets.LambdaTarget(analysis_lambda))

        # CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self, "SDLCDashboard",
            dashboard_name="sdlc-automation-dashboard"
        )

        # Add metrics to dashboard
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Invocations",
                left=[
                    webhook_lambda.metric_invocations(
                        statistic="Sum",
                        period=Duration.minutes(5)
                    ),
                    analysis_lambda.metric_invocations(
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                ]
            ),
            cloudwatch.GraphWidget(
                title="Lambda Errors",
                left=[
                    webhook_lambda.metric_errors(statistic="Sum"),
                    analysis_lambda.metric_errors(statistic="Sum")
                ]
            ),
            cloudwatch.GraphWidget(
                title="Lambda Duration",
                left=[
                    webhook_lambda.metric_duration(statistic="Average"),
                    analysis_lambda.metric_duration(statistic="Average")
                ]
            )
        )

        # CloudWatch Log Groups
        webhook_logs = logs.LogGroup(
            self, "WebhookLogs",
            retention=logs.RetentionDays.TWO_WEEKS
        )

        analysis_logs = logs.LogGroup(
            self, "AnalysisLogs",
            retention=logs.RetentionDays.ONE_MONTH
        )

        # Add tags
        Tags.of(self).add("Project", "SDLC-Automation")
        Tags.of(self).add("Environment", "Production")
        Tags.of(self).add("ManagedBy", "CDK")


# CDK App configuration example:
"""
from aws_cdk import App

app = App()
SDLCAutomationStack(app, "SDLCAutomationStack")
app.synth()

Deploy with: cdk deploy --require-approval never
"""
