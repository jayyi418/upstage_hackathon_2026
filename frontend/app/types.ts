export interface TestResult {
  name: string
  original_term?: string
  value: string
  unit: string
  normal_range?: string
  status: 'normal' | 'high' | 'low'
  plain_explanation: string
}

export interface Medication {
  name: string
  dosage_instruction?: string
  purpose: string
}

export interface RichTranslation {
  summary: string
  test_results: TestResult[]
  medications: Medication[]
  action_items: string[]
  full_explanation: string
}

export interface RiskAssessment {
  diagnosis: string
  level: 'low' | 'medium' | 'high'
  reason: string
}

export interface AnalysisResult {
  parsed_text: string
  rich_translation: RichTranslation
  risk_assessments: RiskAssessment[]
  extracted_info: {
    diagnoses: string[]
    patient_name?: string
    hospital?: string
    date?: string
  }
}

export interface Sample {
  key: string
  label: string
}
