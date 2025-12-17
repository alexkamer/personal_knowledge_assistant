/**
 * Tests for MetadataBadges component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { MetadataBadges } from './MetadataBadges';

describe('MetadataBadges', () => {
  describe('Rendering', () => {
    it('should return null when no props are provided', () => {
      const { container } = render(<MetadataBadges />);

      expect(container.firstChild).toBeNull();
    });

    it('should return null when all props are undefined', () => {
      const { container } = render(
        <MetadataBadges contentType={undefined} hasCode={undefined} semanticDensity={undefined} />
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Content Type Badge', () => {
    it('should render paragraph badge', () => {
      render(<MetadataBadges contentType="paragraph" />);

      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.getByTitle('Content type: Paragraph')).toBeInTheDocument();
    });

    it('should render list badge', () => {
      render(<MetadataBadges contentType="list" />);

      expect(screen.getByText('List')).toBeInTheDocument();
      expect(screen.getByTitle('Content type: List')).toBeInTheDocument();
    });

    it('should render heading badge', () => {
      render(<MetadataBadges contentType="heading" />);

      expect(screen.getByText('Heading')).toBeInTheDocument();
      expect(screen.getByTitle('Content type: Heading')).toBeInTheDocument();
    });

    it('should render code badge for content type', () => {
      render(<MetadataBadges contentType="code" />);

      const codeBadges = screen.getAllByText('Code');
      expect(codeBadges.length).toBe(1);
      expect(screen.getByTitle('Content type: Code')).toBeInTheDocument();
    });

    it('should render table badge', () => {
      render(<MetadataBadges contentType="table" />);

      expect(screen.getByText('Table')).toBeInTheDocument();
      expect(screen.getByTitle('Content type: Table')).toBeInTheDocument();
    });

    it('should not render badge for unknown content type', () => {
      const { container } = render(<MetadataBadges contentType="unknown" />);

      expect(container.firstChild).toBeNull();
    });

    it('should render with correct color classes for paragraph', () => {
      const { container } = render(<MetadataBadges contentType="paragraph" />);

      const badge = container.querySelector('.bg-stone-100');
      expect(badge).toBeInTheDocument();
    });

    it('should render with correct color classes for list', () => {
      const { container } = render(<MetadataBadges contentType="list" />);

      const badge = container.querySelector('.bg-purple-100');
      expect(badge).toBeInTheDocument();
    });

    it('should render with correct color classes for heading', () => {
      const { container } = render(<MetadataBadges contentType="heading" />);

      const badge = container.querySelector('.bg-indigo-100');
      expect(badge).toBeInTheDocument();
    });

    it('should render with correct color classes for code', () => {
      const { container } = render(<MetadataBadges contentType="code" />);

      const badge = container.querySelector('.bg-green-100');
      expect(badge).toBeInTheDocument();
    });

    it('should render with correct color classes for table', () => {
      const { container } = render(<MetadataBadges contentType="table" />);

      const badge = container.querySelector('.bg-blue-100');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Has Code Badge', () => {
    it('should render code badge when hasCode is true', () => {
      render(<MetadataBadges hasCode={true} />);

      expect(screen.getByText('Code')).toBeInTheDocument();
      expect(screen.getByTitle('Contains code')).toBeInTheDocument();
    });

    it('should not render code badge when hasCode is false', () => {
      const { container } = render(<MetadataBadges hasCode={false} />);

      expect(container.firstChild).toBeNull();
    });

    it('should not render separate code badge when contentType is already code', () => {
      render(<MetadataBadges contentType="code" hasCode={true} />);

      const codeBadges = screen.getAllByText('Code');
      expect(codeBadges.length).toBe(1); // Only one code badge
    });

    it('should render both badges when hasCode is true and contentType is not code', () => {
      render(<MetadataBadges contentType="paragraph" hasCode={true} />);

      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.getByText('Code')).toBeInTheDocument();
    });
  });

  describe('Semantic Density Badge', () => {
    it('should render high density badge', () => {
      render(<MetadataBadges semanticDensity={0.8} />);

      expect(screen.getByText('High Density')).toBeInTheDocument();
      expect(screen.getByTitle(/Semantic density: 80%/)).toBeInTheDocument();
    });

    it('should render medium density badge', () => {
      render(<MetadataBadges semanticDensity={0.5} />);

      expect(screen.getByText('Medium Density')).toBeInTheDocument();
      expect(screen.getByTitle(/Semantic density: 50%/)).toBeInTheDocument();
    });

    it('should render low density badge', () => {
      render(<MetadataBadges semanticDensity={0.3} />);

      expect(screen.getByText('Low Density')).toBeInTheDocument();
      expect(screen.getByTitle(/Semantic density: 30%/)).toBeInTheDocument();
    });

    it('should use correct color for high density', () => {
      const { container } = render(<MetadataBadges semanticDensity={0.8} />);

      const badge = container.querySelector('.bg-orange-100');
      expect(badge).toBeInTheDocument();
    });

    it('should use correct color for medium density', () => {
      const { container } = render(<MetadataBadges semanticDensity={0.5} />);

      const badge = container.querySelector('.bg-amber-100');
      expect(badge).toBeInTheDocument();
    });

    it('should use correct color for low density', () => {
      const { container } = render(<MetadataBadges semanticDensity={0.3} />);

      const badge = container.querySelector('.bg-yellow-100');
      expect(badge).toBeInTheDocument();
    });

    it('should handle density at boundary (0.7)', () => {
      render(<MetadataBadges semanticDensity={0.7} />);

      expect(screen.getByText('Medium Density')).toBeInTheDocument();
    });

    it('should handle density at boundary (0.4)', () => {
      render(<MetadataBadges semanticDensity={0.4} />);

      expect(screen.getByText('Low Density')).toBeInTheDocument();
    });

    it('should handle density at boundary (0.71)', () => {
      render(<MetadataBadges semanticDensity={0.71} />);

      expect(screen.getByText('High Density')).toBeInTheDocument();
    });

    it('should handle density at boundary (0.41)', () => {
      render(<MetadataBadges semanticDensity={0.41} />);

      expect(screen.getByText('Medium Density')).toBeInTheDocument();
    });

    it('should handle zero density', () => {
      render(<MetadataBadges semanticDensity={0} />);

      expect(screen.getByText('Low Density')).toBeInTheDocument();
      expect(screen.getByTitle(/Semantic density: 0%/)).toBeInTheDocument();
    });

    it('should handle maximum density', () => {
      render(<MetadataBadges semanticDensity={1} />);

      expect(screen.getByText('High Density')).toBeInTheDocument();
      expect(screen.getByTitle(/Semantic density: 100%/)).toBeInTheDocument();
    });

    it('should not render density badge when semanticDensity is null', () => {
      const { container } = render(<MetadataBadges semanticDensity={null as any} />);

      expect(container.firstChild).toBeNull();
    });

    it('should not render density badge when semanticDensity is undefined', () => {
      const { container } = render(<MetadataBadges semanticDensity={undefined} />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Multiple Badges', () => {
    it('should render all badges when all props are provided', () => {
      render(<MetadataBadges contentType="paragraph" hasCode={true} semanticDensity={0.6} />);

      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.getByText('Code')).toBeInTheDocument();
      expect(screen.getByText('Medium Density')).toBeInTheDocument();
    });

    it('should render content type and density badges', () => {
      render(<MetadataBadges contentType="list" semanticDensity={0.8} />);

      expect(screen.getByText('List')).toBeInTheDocument();
      expect(screen.getByText('High Density')).toBeInTheDocument();
    });

    it('should render hasCode and density badges', () => {
      render(<MetadataBadges hasCode={true} semanticDensity={0.2} />);

      expect(screen.getByText('Code')).toBeInTheDocument();
      expect(screen.getByText('Low Density')).toBeInTheDocument();
    });

    it('should render badges in a flex container', () => {
      const { container } = render(<MetadataBadges contentType="paragraph" hasCode={true} />);

      const flexContainer = container.querySelector('.flex.flex-wrap');
      expect(flexContainer).toBeInTheDocument();
    });
  });

  describe('Icons', () => {
    it('should render FileText icon for paragraph', () => {
      const { container } = render(<MetadataBadges contentType="paragraph" />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render List icon for list', () => {
      const { container } = render(<MetadataBadges contentType="list" />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render Heading icon for heading', () => {
      const { container } = render(<MetadataBadges contentType="heading" />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render Code icon for code', () => {
      const { container } = render(<MetadataBadges contentType="code" />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render Table icon for table', () => {
      const { container } = render(<MetadataBadges contentType="table" />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render Layers icon for density', () => {
      const { container } = render(<MetadataBadges semanticDensity={0.5} />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have title attribute for content type', () => {
      render(<MetadataBadges contentType="paragraph" />);

      const badge = screen.getByTitle('Content type: Paragraph');
      expect(badge).toBeInTheDocument();
    });

    it('should have title attribute for hasCode', () => {
      render(<MetadataBadges hasCode={true} />);

      const badge = screen.getByTitle('Contains code');
      expect(badge).toBeInTheDocument();
    });

    it('should have descriptive title for semantic density', () => {
      render(<MetadataBadges semanticDensity={0.75} />);

      const badge = screen.getByTitle(/Semantic density: 75% \(information richness\)/);
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle very small semantic density', () => {
      render(<MetadataBadges semanticDensity={0.001} />);

      expect(screen.getByText('Low Density')).toBeInTheDocument();
      expect(screen.getByTitle(/Semantic density: 0%/)).toBeInTheDocument();
    });

    it('should handle semantic density slightly above 1', () => {
      render(<MetadataBadges semanticDensity={1.5} />);

      expect(screen.getByText('High Density')).toBeInTheDocument();
      expect(screen.getByTitle(/Semantic density: 150%/)).toBeInTheDocument();
    });

    it('should handle negative semantic density', () => {
      render(<MetadataBadges semanticDensity={-0.5} />);

      expect(screen.getByText('Low Density')).toBeInTheDocument();
    });

    it('should handle empty string content type', () => {
      const { container } = render(<MetadataBadges contentType="" />);

      expect(container.firstChild).toBeNull();
    });

    it('should handle hasCode as false with other props', () => {
      render(<MetadataBadges contentType="paragraph" hasCode={false} semanticDensity={0.5} />);

      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.queryByTitle('Contains code')).not.toBeInTheDocument();
      expect(screen.getByText('Medium Density')).toBeInTheDocument();
    });
  });
});
